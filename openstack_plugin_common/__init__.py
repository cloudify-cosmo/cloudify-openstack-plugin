#########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.

from functools import wraps
import logging
import random
import string
import time
import unittest
import json
import os

import keystoneclient.v2_0.client as keystone_client
import neutronclient.v2_0.client as neutron_client
import neutronclient.common.exceptions as neutron_exceptions
import novaclient.v1_1.client as nova_client
import novaclient.exceptions as nova_exceptions

import cloudify.manager
import cloudify.decorators

PREFIX_RANDOM_CHARS = 3
CLEANUP_RETRIES = 10
CLEANUP_RETRY_SLEEP = 2


class ProviderContext(object):

    def __init__(self, provider_context):
        self._provider_context = provider_context or {}
        self._resources = self._provider_context.get('resources', {})

    @property
    def agents_keypair(self):
        return self._provider_context.get('agents_keypair')

    @property
    def agents_security_group(self):
        return self._provider_context.get('agents_security_group')

    @property
    def ext_network(self):
        return self._provider_context.get('ext_network')

    @property
    def floating_ip(self):
        return self._provider_context.get('floating_ip')

    @property
    def int_network(self):
        return self._provider_context.get('int_network')

    @property
    def management_keypair(self):
        return self._provider_context.get('management_keypair')

    @property
    def management_security_group(self):
        return self._provider_context.get('management_security_group')

    @property
    def management_server(self):
        return self._provider_context.get('management_server')

    @property
    def router(self):
        return self._provider_context.get('router')

    @property
    def subnet(self):
        return self._provider_context.get('subnet')


def provider(ctx):
    provider_context = ctx.get_provider_context('cloudify_openstack')
    return ProviderContext(provider_context)


class Config(object):
    def get(self):
        which = self.__class__.which
        env_name = which.upper() + '_CONFIG_PATH'
        default_location_tpl = '~/' + which + '_config.json'
        default_location = os.path.expanduser(default_location_tpl)
        config_path = os.getenv(env_name, default_location)
        try:
            with open(config_path) as f:
                cfg = json.loads(f.read())
        except IOError:
            raise RuntimeError(
                "Failed to read {0} configuration from file '{1}'."
                "The configuration is looked up in {2}. If defined, "
                "environment variable "
                "{3} overrides that location.".format(
                    which, config_path, default_location_tpl, env_name))
        return cfg


class KeystoneConfig(Config):
    which = 'keystone'


class NeutronConfig(Config):
    which = 'neutron'


class TestsConfig(Config):
    which = 'os_tests'


class OpenStackClient(object):
    def get(self, config=None, *args, **kw):
        static_config = self.__class__.config().get()
        cfg = {}
        cfg.update(static_config)
        if config:
            cfg.update(config)
        ret = self.connect(cfg, *args, **kw)
        ret.format = 'json'
        return ret


# Clients acquireres


class KeystoneClient(OpenStackClient):

    config = KeystoneConfig

    def connect(self, cfg):
        args = {field: cfg[field] for field in (
            'username', 'password', 'tenant_name', 'auth_url')}
        return keystone_client.Client(**args)


class NovaClient(OpenStackClient):

    config = KeystoneConfig

    def connect(self, cfg, region=None):
        return nova_client.Client(username=cfg['username'],
                                  api_key=cfg['password'],
                                  project_id=cfg['tenant_name'],
                                  auth_url=cfg['auth_url'],
                                  region_name=region or cfg['region'],
                                  http_log_debug=False)


def _nova_exception_handler(exception):
    if not isinstance(exception, nova_exceptions.OverLimit):
        raise
    retry_after = exception.retry_after
    if retry_after == 0:
        retry_after = 5
    return retry_after


class NeutronClient(OpenStackClient):

    config = NeutronConfig

    def connect(self, cfg):
        ks = KeystoneClient().get(config=cfg.get('keystone_config'))
        ret = NeutronClientWithSugar(endpoint_url=cfg['url'],
                                     token=ks.auth_token)
        ret.format = 'json'
        return ret


def neutron_exception_handler(exception):
    if not isinstance(exception, neutron_exceptions.NeutronClientException):
        raise
    if exception.message is not None and \
            'TokenRateLimit' not in exception.message:
        raise
    retry_after = 30
    return retry_after


# Decorators

def _find_instanceof_in_kw(cls, kw):
    ret = [v for v in kw.values() if isinstance(v, cls)]
    if not ret:
        return None
    if len(ret) > 1:
        raise RuntimeError(
            "Expected to find exactly one instance of {0} in "
            "kwargs but found {1}".format(cls, len(ret)))
    return ret[0]


def _find_context_in_kw(kw):
    return _find_instanceof_in_kw(cloudify.context.CloudifyContext, kw)


def with_neutron_client(f):
    @wraps(f)
    def wrapper(*args, **kw):
        ctx = _find_context_in_kw(kw)
        if ctx:
            config = ctx.properties.get('neutron_config')
            logger = ctx.logger
        else:
            config = None
            logger = None
        neutron_client = ExceptionRetryProxy(
            NeutronClient().get(config=config),
            exception_handler=neutron_exception_handler,
            logger=logger)
        kw['neutron_client'] = neutron_client
        return f(*args, **kw)
    return wrapper


def with_nova_client(f):
    @wraps(f)
    def wrapper(*args, **kw):
        ctx = _find_context_in_kw(kw)
        if ctx:
            logger = ctx.logger
            config = ctx.properties.get('nova_config')
        else:
            config = None
            logger = None

        nova_client = NovaClient().get(config=config)

        nova_client.servers_proxy = ExceptionRetryProxy(
            nova_client.servers,
            exception_handler=_nova_exception_handler,
            logger=logger)
        nova_client.images_proxy = ExceptionRetryProxy(
            nova_client.images,
            exception_handler=_nova_exception_handler,
            logger=logger)
        nova_client.flavors_proxy = ExceptionRetryProxy(
            nova_client.flavors,
            exception_handler=_nova_exception_handler,
            logger=logger)

        kw['nova_client'] = nova_client
        return f(*args, **kw)
    return wrapper

# Sugar for clients


class NeutronClientWithSugar(neutron_client.Client):

    def cosmo_plural(self, obj_type_single):
        return obj_type_single + 's'

    def cosmo_get_named(self, obj_type_single, name, **kw):
        return self.cosmo_get(obj_type_single, name=name, **kw)

    def cosmo_get(self, obj_type_single, **kw):
        ls = list(self.cosmo_list(obj_type_single, **kw))
        if len(ls) != 1:
            raise RuntimeError(
                "Expected exactly one object of type {0} "
                "with match {1} but there are {2}".format(
                    obj_type_single, kw, len(ls)))
        return ls[0]

    def cosmo_list(self, obj_type_single, **kw):
        """ Sugar for list_XXXs()['XXXs'] """
        obj_type_plural = self.cosmo_plural(obj_type_single)
        for obj in getattr(self, 'list_' + obj_type_plural)(**kw)[
                obj_type_plural]:
            yield obj

    def cosmo_list_prefixed(self, obj_type_single, name_prefix):
        for obj in self.cosmo_list(obj_type_single):
            if obj['name'].startswith(name_prefix):
                yield obj

    def cosmo_delete_prefixed(self, name_prefix):
        # Cleanup all neutron.list_XXX() objects with names starting
        #  with self.name_prefix
        for obj_type_single in 'port', 'router', 'network', 'subnet',\
                               'security_group':
            for obj in self.cosmo_list_prefixed(obj_type_single, name_prefix):
                if obj_type_single == 'router':
                    ports = self.cosmo_list('port', device_id=obj['id'])
                    for port in ports:
                        try:
                            self.remove_interface_router(
                                port['device_id'],
                                {'port_id': port['id']})
                        except neutron_exceptions.NeutronClientException:
                            pass
                getattr(self, 'delete_' + obj_type_single)(obj['id'])

    def cosmo_find_external_net(self):
        """ For tests of floating IP """
        nets = self.list_networks()['networks']
        ls = [net for net in nets if net.get('router:external')]
        if len(ls) == 1:
            return ls[0]
        if len(ls) != 1:
            raise RuntimeError(
                "Expected exactly one external network but found {0}".format(
                    len(ls)))

    def cosmo_is_network(self, id):
        return any(self.cosmo_list('network', id=id))

    def cosmo_is_port(self, id):
        return any(self.cosmo_list('port', id=id))


class TrackingNeutronClientWithSugar(NeutronClientWithSugar):

    _cosmo_undo = []  # Tuples of (func, args, kwargs) to run for cleanup

    def __init__(self, *args, **kw):
        return super(TrackingNeutronClientWithSugar, self).__init__(
            *args, **kw)

    def create_floatingip(self, *args, **kw):
        ret = super(TrackingNeutronClientWithSugar, self).create_floatingip(
            *args, **kw)
        self.__class__._cosmo_undo.append(
            (self.delete_floatingip, (ret['floatingip']['id'],), {}))
        return ret

    def cosmo_delete_tracked(self):
        for f, args, kw in self.__class__._cosmo_undo:
            try:
                f(*args, **kw)
            except neutron_exceptions.NeutronClientException:
                pass


class ExceptionRetryProxy(object):

    def __init__(self, delegate, exception_handler, logger=None):
        self.delegate = delegate
        self.logger = logger
        self.exception_handler = exception_handler

    def __getattr__(self, name):
        attr = getattr(self.delegate, name)
        if callable(attr):
            def wrapper(*args, **kwargs):
                retries = 5
                for i in range(retries):
                    try:
                        return attr(*args, **kwargs)
                    except Exception, e:
                        if i == retries - 1:
                            break
                        retry_after = self.exception_handler(e)
                        retry_after += random.randint(0, retry_after)
                        if self.logger is not None:
                            message = '{0} exception caught while ' \
                                      'executing {1}. sleeping for {2} ' \
                                      'seconds before trying again (Attempt' \
                                      ' {3}/{4})'.format(type(e),
                                                         name,
                                                         retry_after,
                                                         i+2,
                                                         retries)
                            self.logger.warn(message)
                        time.sleep(retry_after)
                raise
            return wrapper
        return attr


class ExceptionRetryProxyTestCase(unittest.TestCase):

    class MockClient(object):
        def __init__(self):
            self.attribute = 'attribute'

        def raise_over_limit(self, retry_after=None):
            if retry_after is not None:
                raise nova_exceptions.OverLimit(code=413,
                                                retry_after=retry_after)
            else:
                raise nova_exceptions.OverLimit(code=413)

        def normal_method(self):
            return 'normal'

        def raise_other(self):
            raise RuntimeError()

    def setUp(self):
        random.seed(0)
        logging.basicConfig()
        logger = logging.getLogger('test')
        logger.setLevel(logging.DEBUG)
        self.client = ExceptionRetryProxy(
            self.MockClient(),
            exception_handler=_nova_exception_handler,
            logger=logger)

    def test(self):
        self.assertRaises(AttributeError,
                          lambda: self.client.non_existent_attribute)

        start = time.time()
        self.assertEqual(self.client.attribute, 'attribute')
        self.assertLess(time.time() - start, 0.5)

        start = time.time()
        self.assertEqual(self.client.normal_method(), 'normal')
        self.assertLess(time.time() - start, 0.5)

        start = time.time()
        self.assertRaises(RuntimeError, self.client.raise_other)
        self.assertLess(time.time() - start, 0.5)

        start = time.time()
        self.assertRaises(nova_exceptions.OverLimit,
                          self.client.raise_over_limit,
                          retry_after=1)
        # timing relies on # random.seed(0)
        self.assertGreater(time.time() - start, 6)
        self.assertLess(time.time() - start, 7)

        # timing relies on # random.seed(0)
        start = time.time()
        self.assertRaises(nova_exceptions.OverLimit,
                          self.client.raise_over_limit)
        self.assertGreater(time.time() - start, 13)


class TestCase(unittest.TestCase):

    def get_nova_client(self):
        r = NovaClient().get()
        self.get_nova_client = lambda: r
        return self.get_nova_client()

    def get_neutron_client(self):
        r = NeutronClient().get()
        self.get_neutron_client = lambda: r
        return self.get_neutron_client()

    def _mock_send_event(self, *args, **kw):
        self.logger.debug("_mock_send_event(args={0}, kw={1})".format(
            args, kw))

    def _mock_get_node_state(self, __cloudify_id, *args, **kw):
        self.logger.debug(
            "_mock_get_node_state(__cloudify_id={0} args={1}, kw={2})".format(
                __cloudify_id, args, kw))
        return self.nodes_data[__cloudify_id]

    def setUp(self):
        # Careful!
        globals()['NeutronClientWithSugar'] = TrackingNeutronClientWithSugar
        logger = logging.getLogger(__name__)
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logger
        self.logger.level = logging.DEBUG
        self.logger.debug("Cosmo test setUp() called")
        chars = string.ascii_uppercase + string.digits
        self.name_prefix = 'cosmo_test_{0}_'\
            .format(''.join(
                random.choice(chars) for x in range(PREFIX_RANDOM_CHARS)))
        self.timeout = 120

        self.logger.debug("Cosmo test setUp() done")

    def tearDown(self):
        self.logger.debug("Cosmo test tearDown() called")
        servers_list = self.get_nova_client().servers.list()
        for server in servers_list:
            if server.name.startswith(self.name_prefix):
                self.logger.info("Deleting server with name " + server.name)
                try:
                    server.delete()
                except BaseException:
                    self.logger.warning("Failed to delete server with name "
                                        + server.name)
            else:
                self.logger.info("NOT deleting server with name "
                                 + server.name)
        for i in range(1, CLEANUP_RETRIES+1):
            try:
                self.logger.debug(
                    "Neutron resources cleanup attempt {0}/{1}"
                    .format(i, CLEANUP_RETRIES)
                )
                NeutronClient().get().cosmo_delete_prefixed(self.name_prefix)
                NeutronClient().get().cosmo_delete_tracked()
                break
            except neutron_exceptions.NetworkInUseClient:
                pass
            time.sleep(CLEANUP_RETRY_SLEEP)
        self.logger.debug("Cosmo test tearDown() done")

    @with_neutron_client
    def create_network(self, name_suffix, neutron_client):
        return neutron_client.create_network({'network': {
            'name': self.name_prefix + name_suffix, 'admin_state_up': True
        }})['network']

    @with_neutron_client
    def create_subnet(self, name_suffix, cidr, neutron_client, network=None):
        if not network:
            network = self.create_network(name_suffix)
        return neutron_client.create_subnet({
            'subnet': {
                'name': self.name_prefix + name_suffix,
                'ip_version': 4,
                'cidr': cidr,
                'network_id': network['id']
            }
        })['subnet']

    @with_neutron_client
    def create_port(self, name_suffix, network, neutron_client):
        return neutron_client.create_port({
            'port': {
                'name': self.name_prefix + name_suffix,
                'network_id': network['id']
            }
        })['port']

    @with_neutron_client
    def create_sg(self, name_suffix, neutron_client):
        return neutron_client.create_security_group({
            'security_group': {
                'name': self.name_prefix + name_suffix,
            }
        })['security_group']

    @with_neutron_client
    def assertThereIsOneAndGet(self, obj_type_single, neutron_client, **kw):
        objs = list(neutron_client.cosmo_list(obj_type_single, **kw))
        self.assertEquals(1, len(objs))
        return objs[0]

    assertThereIsOne = assertThereIsOneAndGet

    @with_neutron_client
    def assertThereIsNo(self, obj_type_single, neutron_client, **kw):
        objs = list(neutron_client.cosmo_list(obj_type_single, **kw))
        self.assertEquals(0, len(objs))

    @with_nova_client
    def assertThereIsOneServerAndGet(self, nova_client, **kw):
        servers = nova_client.servers.findall(**kw)
        self.assertEquals(1, len(servers))
        return servers[0]

    assertThereIsOneServer = assertThereIsOneServerAndGet

    @with_nova_client
    def assertThereIsNoServer(self, nova_client, **kw):
        servers = nova_client.servers.findall(**kw)
        self.assertEquals(0, len(servers))
