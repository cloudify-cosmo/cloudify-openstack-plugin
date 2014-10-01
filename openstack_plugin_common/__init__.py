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
import json
import os
import sys

import keystoneclient.v2_0.client as keystone_client
import neutronclient.v2_0.client as neutron_client
import neutronclient.common.exceptions as neutron_exceptions
import novaclient.v1_1.client as nova_client
import novaclient.exceptions as nova_exceptions

import cloudify
from cloudify.exceptions import NonRecoverableError, RecoverableError

# properties
USE_EXTERNAL_RESOURCE_PROPERTY = 'use_external_resource'

# runtime properties
OPENSTACK_ID_PROPERTY = 'external_id'  # resource's openstack id
OPENSTACK_TYPE_PROPERTY = 'external_type'  # resource's openstack type
OPENSTACK_NAME_PROPERTY = 'external_name'  # resource's openstack name

# runtime properties which all types use
COMMON_RUNTIME_PROPERTIES_KEYS = [OPENSTACK_ID_PROPERTY,
                                  OPENSTACK_TYPE_PROPERTY,
                                  OPENSTACK_NAME_PROPERTY]


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


def get_openstack_ids_of_connected_nodes_by_openstack_type(ctx, type_name):
    type_caps = [caps for caps in ctx.capabilities.get_all().values() if
                 caps.get(OPENSTACK_TYPE_PROPERTY) == type_name]
    return [cap[OPENSTACK_ID_PROPERTY] for cap in type_caps]


def get_openstack_id_of_single_connected_node_by_openstack_type(
        ctx, type_name, if_exists=False):
    ids = get_openstack_ids_of_connected_nodes_by_openstack_type(ctx,
                                                                 type_name)
    check = len(ids) > 1 if if_exists else len(ids) != 1
    if check:
        raise NonRecoverableError(
            'Expected {0} one {1} capability. got {2}'.format(
                'at most' if if_exists else 'exactly', type_name, len(ids)))
    return ids[0] if ids else None


def get_resource_id(ctx, type_name):
    if ctx.properties['resource_id']:
        return ctx.properties['resource_id']
    return "{0}_{1}_{2}".format(type_name, ctx.deployment_id, ctx.node_id)


def transform_resource_name(ctx, res):

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


def use_external_resource(ctx, sugared_client, openstack_type):
    if not is_external_resource(ctx):
        return None

    resource_id = ctx.properties['resource_id']
    if not resource_id:
        raise NonRecoverableError(
            "Can't set '{0}' to True without supplying a value for "
            "'resource_id'".format(USE_EXTERNAL_RESOURCE_PROPERTY))

    from neutron_plugin.floatingip import FLOATINGIP_OPENSTACK_TYPE
    if openstack_type != FLOATINGIP_OPENSTACK_TYPE:
        # search for resource by name
        resource = sugared_client.cosmo_get_if_exists(
            openstack_type, name=resource_id)
    else:
        # search for resource by ip address
        resource = sugared_client.cosmo_get_if_exists(
            openstack_type, floating_ip_address=resource_id)

    if not resource:
        # fallback - search for resource by id
        resource = sugared_client.cosmo_get_if_exists(
            openstack_type, id=resource_id)

    if not resource:
        raise NonRecoverableError("Couldn't find a resource with the name or "
                                  "id {0}".format(resource_id))

    ctx.runtime_properties[OPENSTACK_ID_PROPERTY] = \
        sugared_client.get_id_from_resource(resource)
    ctx.runtime_properties[OPENSTACK_TYPE_PROPERTY] = openstack_type

    if openstack_type != FLOATINGIP_OPENSTACK_TYPE:
        ctx.runtime_properties[OPENSTACK_NAME_PROPERTY] = \
            sugared_client.get_name_from_resource(resource)

    ctx.logger.info('Using external resource {0}: {1}'.format(
        openstack_type, resource_id))
    return resource


def delete_resource_and_runtime_properties(ctx, sugared_client,
                                           runtime_properties_keys):
    node_openstack_type = ctx.runtime_properties[OPENSTACK_TYPE_PROPERTY]
    if not is_external_resource(ctx):
        ctx.logger.info('deleting {0}'.format(node_openstack_type))
        sugared_client.cosmo_delete_resource(
            node_openstack_type, ctx.runtime_properties[OPENSTACK_ID_PROPERTY])
    else:
        ctx.logger.info('not deleting {0} since an external {0} is '
                        'being used'.format(node_openstack_type))

    delete_runtime_properties(ctx, runtime_properties_keys)


def is_external_resource(ctx):
    return is_external_resource_by_properties(ctx.properties)


def is_external_relationship(ctx):
    return is_external_resource_by_properties(
        ctx.properties) and is_external_resource_by_properties(
        ctx.related.properties)


def is_external_resource_by_properties(properties):
    return USE_EXTERNAL_RESOURCE_PROPERTY in properties and \
        properties[USE_EXTERNAL_RESOURCE_PROPERTY]


def delete_runtime_properties(ctx, runtime_properties_keys):
    for runtime_prop_key in runtime_properties_keys:
        if runtime_prop_key in ctx.runtime_properties:
            del ctx.runtime_properties[runtime_prop_key]


class Config(object):

    OPENSTACK_CONFIG_PATH_ENV_VAR = 'OPENSTACK_CONFIG_PATH'
    OPENSTACK_CONFIG_PATH_DEFAULT_PATH = '~/openstack_config.json'

    def get(self):
        static_config = self._build_config_from_env_variables()
        env_name = self.OPENSTACK_CONFIG_PATH_ENV_VAR
        default_location_tpl = self.OPENSTACK_CONFIG_PATH_DEFAULT_PATH
        default_location = os.path.expanduser(default_location_tpl)
        config_path = os.getenv(env_name, default_location)
        try:
            with open(config_path) as f:
                Config.update_config(static_config, json.loads(f.read()))
        except IOError:
            pass
        return static_config

    @staticmethod
    def _build_config_from_env_variables():
        cfg = dict()

        def take_env_var_if_exists(cfg_key, env_var):
            if env_var in os.environ:
                cfg[cfg_key] = os.environ[env_var]

        take_env_var_if_exists('username', 'OS_USERNAME')
        take_env_var_if_exists('password', 'OS_PASSWORD')
        take_env_var_if_exists('tenant_name', 'OS_TENANT_NAME')
        take_env_var_if_exists('auth_url', 'OS_AUTH_URL')

        return cfg

    @staticmethod
    def update_config(overridden_cfg, overriding_cfg):
        """ this method is like dict.update() only that it doesn't override
        with (or set new) empty values (e.g. empty string) """
        for k, v in overriding_cfg.iteritems():
            if v:
                overridden_cfg[k] = v


class OpenStackClient(object):
    def get(self, config=None, *args, **kw):
        cfg = Config().get()
        if config:
            Config.update_config(cfg, config)

        self._validate_config(cfg)
        ret = self.connect(cfg, *args, **kw)
        ret.format = 'json'
        return ret

    def _validate_config(self, cfg):
        missing_config_params = \
            [param for param in self.REQUIRED_CONFIG_PARAMS if param not in
             cfg or not cfg[param]]

        if missing_config_params:
            raise NonRecoverableError(
                "Missing Openstack configuration parameters: {0}; "
                "Expected to find parameters either as environment "
                "variables, in a JSON file (at either a path which is "
                "set under the environment variable {1} or at the "
                "default location {2}), or as nested properties under "
                "a 'openstack_config' property".format(
                    missing_config_params,
                    Config.OPENSTACK_CONFIG_PATH_ENV_VAR,
                    Config.OPENSTACK_CONFIG_PATH_DEFAULT_PATH))


# Clients acquireres
class KeystoneClient(OpenStackClient):

    REQUIRED_CONFIG_PARAMS = \
        ['username', 'password', 'tenant_name', 'auth_url']

    def connect(self, cfg):
        args = {field: cfg[field] for field in self.REQUIRED_CONFIG_PARAMS}
        return keystone_client.Client(**args)


class NovaClient(OpenStackClient):

    REQUIRED_CONFIG_PARAMS = \
        ['username', 'password', 'tenant_name', 'auth_url', 'region']

    def connect(self, cfg, region=None):
        return NovaClientWithSugar(username=cfg['username'],
                                   api_key=cfg['password'],
                                   project_id=cfg['tenant_name'],
                                   auth_url=cfg['auth_url'],
                                   region_name=region or cfg['region'],
                                   http_log_debug=False)


class NeutronClient(OpenStackClient):

    REQUIRED_CONFIG_PARAMS = \
        ['username', 'password', 'tenant_name', 'auth_url', 'region']

    def connect(self, cfg):
        return NeutronClientWithSugar(username=cfg['username'],
                                      password=cfg['password'],
                                      tenant_name=cfg['tenant_name'],
                                      auth_url=cfg['auth_url'],
                                      region_name=cfg['region'])


# Decorators
def _find_instanceof_in_kw(cls, kw):
    ret = [v for v in kw.values() if isinstance(v, cls)]
    if not ret:
        return None
    if len(ret) > 1:
        raise NonRecoverableError(
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
            config = ctx.properties.get('openstack_config')
        else:
            config = None
        kw['neutron_client'] = NeutronClient().get(config=config)
        try:
            return f(*args, **kw)
        except neutron_exceptions.NeutronClientException, e:
            if e.status_code in _non_recoverable_error_codes:
                _re_raise(e, recoverable=False)
            else:
                raise
    return wrapper


def with_nova_client(f):
    @wraps(f)
    def wrapper(*args, **kw):
        ctx = _find_context_in_kw(kw)
        if ctx:
            config = ctx.properties.get('openstack_config')
        else:
            config = None
        kw['nova_client'] = NovaClient().get(config=config)
        try:
            return f(*args, **kw)
        except nova_exceptions.OverLimit, e:
            _re_raise(e, recoverable=True, retry_after=e.retry_after)
        except nova_exceptions.ClientException, e:
            if e.code in _non_recoverable_error_codes:
                _re_raise(e, recoverable=False)
            else:
                raise
    return wrapper

_non_recoverable_error_codes = [400, 401, 403, 404, 409]


def _re_raise(e, recoverable, retry_after=None):
    exc_type, exc, traceback = sys.exc_info()
    if recoverable:
        if retry_after == 0:
            retry_after = None
        raise RecoverableError(
            message=e.message,
            retry_after=retry_after), None, traceback
    else:
        raise NonRecoverableError(e.message), None, traceback


# Sugar for clients

class ClientWithSugar(object):

    def cosmo_plural(self, obj_type_single):
        return obj_type_single + 's'

    def cosmo_get_named(self, obj_type_single, name, **kw):
        return self.cosmo_get(obj_type_single, name=name, **kw)

    def cosmo_get(self, obj_type_single, **kw):
        return self._cosmo_get(obj_type_single, False, **kw)

    def cosmo_get_if_exists(self, obj_type_single, **kw):
        return self._cosmo_get(obj_type_single, True, **kw)

    def _cosmo_get(self, obj_type_single, if_exists, **kw):
        ls = list(self.cosmo_list(obj_type_single, **kw))
        check = len(ls) > 1 if if_exists else len(ls) != 1
        if check:
            raise NonRecoverableError(
                "Expected {0} one object of type {1} "
                "with match {2} but there are {3}".format(
                    'at most' if if_exists else 'exactly',
                    obj_type_single, kw, len(ls)))
        return ls[0] if ls else None


class NovaClientWithSugar(nova_client.Client, ClientWithSugar):

    def cosmo_list(self, obj_type_single, **kw):
        """ Sugar for xxx.findall() - not using xxx.list() because findall
        can receive filtering parameters, and it's common for all types"""
        obj_type_plural = self.cosmo_plural(obj_type_single)
        for obj in getattr(self, obj_type_plural).findall(**kw):
            yield obj

    def cosmo_delete_resource(self, obj_type_single, obj_id):
        obj_type_plural = self.cosmo_plural(obj_type_single)
        getattr(self, obj_type_plural).delete(id=obj_id)

    def get_id_from_resource(self, resource):
        return resource.id

    def get_name_from_resource(self, resource):
        return resource.name


class NeutronClientWithSugar(neutron_client.Client, ClientWithSugar):

    def cosmo_list(self, obj_type_single, **kw):
        """ Sugar for list_XXXs()['XXXs'] """
        obj_type_plural = self.cosmo_plural(obj_type_single)
        for obj in getattr(self, 'list_' + obj_type_plural)(**kw)[
                obj_type_plural]:
            yield obj

    def cosmo_delete_resource(self, obj_type_single, obj_id):
        getattr(self, 'delete_' + obj_type_single)(obj_id)

    def get_id_from_resource(self, resource):
        return resource['id']

    def get_name_from_resource(self, resource):
        return resource['name']

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
        if len(ls) != 1:
            raise NonRecoverableError(
                "Expected exactly one external network but found {0}".format(
                    len(ls)))
        return ls[0]
