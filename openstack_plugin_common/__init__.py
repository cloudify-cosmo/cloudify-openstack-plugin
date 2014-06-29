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
import random
import time
import json
import os

import keystoneclient.v2_0.client as keystone_client
import neutronclient.v2_0.client as neutron_client
import neutronclient.common.exceptions as neutron_exceptions
import novaclient.v1_1.client as nova_client
import novaclient.exceptions as nova_exceptions

import cloudify

OVERLIMIT_DEFAULT_RETRY_AFTER = 5
API_CALL_ATTEMPTS = 5


class ProviderContext(object):

    def __init__(self, provider_context):
        self._provider_context = provider_context or {}
        self._resources = self._provider_context.get('resources', {})

    @property
    def agents_keypair(self):
        return self._resources.get('agents_keypair')

    @property
    def agents_security_group(self):
        return self._resources.get('agents_security_group')

    @property
    def ext_network(self):
        return self._resources.get('ext_network')

    @property
    def floating_ip(self):
        return self._resources.get('floating_ip')

    @property
    def int_network(self):
        return self._resources.get('int_network')

    @property
    def management_keypair(self):
        return self._resources.get('management_keypair')

    @property
    def management_security_group(self):
        return self._resources.get('management_security_group')

    @property
    def management_server(self):
        return self._resources.get('management_server')

    @property
    def router(self):
        return self._resources.get('router')

    @property
    def subnet(self):
        return self._resources.get('subnet')

    def __repr__(self):
        info = json.dumps(self._provider_context)
        return '<' + self.__class__.__name__ + ' ' + info + '>'


def provider(ctx):
    return ProviderContext(ctx.provider_context)


def transform_resource_name(res, ctx):

    if isinstance(res, basestring):
        res = {'name': res}

    if not isinstance(res, dict):
        raise ValueError("transform_resource_name() expects either string or "
                         "dict as the first parameter")

    pfx = ctx.bootstrap_context.resources_prefix

    if not pfx:
        return res['name']

    name = res['name']
    res['name'] = pfx + name

    if name.startswith(pfx):
        ctx.logger.warn("Prefixing resource '{0}' with '{1}' but it "
                        "already has this prefix".format(name, pfx))
    else:
        ctx.logger.info("Transformed resource name '{0}' to '{1}'".format(
                        name, res['name']))

    return res['name']


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
    return exception.retry_after or OVERLIMIT_DEFAULT_RETRY_AFTER


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


def add_proxies_to_nova_client(nova_client, logger):
    for a in 'images', 'servers', 'flavors':
        proxy = ExceptionRetryProxy(
            getattr(nova_client, a),
            exception_handler=_nova_exception_handler,
            logger=logger)
        setattr(nova_client, a + '_proxy', proxy)


def with_nova_client(f):
    @wraps(f)
    def wrapper(*args, **kw):
        ctx = _find_context_in_kw(kw)
        if ctx:
            config = ctx.properties.get('nova_config')
            logger = ctx.logger
        else:
            config = None
            logger = None

        nova_client = NovaClient().get(config=config)
        add_proxies_to_nova_client(nova_client, logger)

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


class ExceptionRetryProxy(object):

    def __init__(self, delegate, exception_handler, logger=None):
        self.delegate = delegate
        self.logger = logger
        self.exception_handler = exception_handler

    def __getattr__(self, name):
        attr = getattr(self.delegate, name)
        if not callable(attr):
            return attr

        def wrapper(*args, **kwargs):
            for i in range(API_CALL_ATTEMPTS):
                try:
                    return attr(*args, **kwargs)
                except Exception, e:
                    if i == API_CALL_ATTEMPTS - 1:
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
                                                     API_CALL_ATTEMPTS)
                        self.logger.warn(message)
                    time.sleep(retry_after)
            raise
        return wrapper
