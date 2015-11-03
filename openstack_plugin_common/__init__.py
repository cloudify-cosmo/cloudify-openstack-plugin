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

from IPy import IP
from cinderclient.v1 import client as cinder_client
from cinderclient import exceptions as cinder_exceptions
import keystoneclient.v2_0.client as keystone_client
import keystoneclient.apiclient.exceptions as keystone_exceptions
import neutronclient.v2_0.client as neutron_client
import neutronclient.common.exceptions as neutron_exceptions
import novaclient.v1_1.client as nova_client
import novaclient.exceptions as nova_exceptions

import cloudify
from cloudify import context
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


def get_connected_nodes_by_openstack_type(ctx, type_name):
    return [rel.target.node for rel in ctx.instance.relationships
            if rel.target.instance.runtime_properties.get(
                OPENSTACK_TYPE_PROPERTY) == type_name]


def get_openstack_ids_of_connected_nodes_by_openstack_type(ctx, type_name):
    type_caps = [caps for caps in ctx.capabilities.get_all().values() if
                 caps.get(OPENSTACK_TYPE_PROPERTY) == type_name]
    return [cap[OPENSTACK_ID_PROPERTY] for cap in type_caps]


def get_single_connected_node_by_openstack_type(
        ctx, type_name, if_exists=False):
    nodes = get_connected_nodes_by_openstack_type(ctx, type_name)
    check = len(nodes) > 1 if if_exists else len(nodes) != 1
    if check:
        raise NonRecoverableError(
            'Expected {0} one {1} node. got {2}'.format(
                'at most' if if_exists else 'exactly', type_name, len(nodes)))
    return nodes[0] if nodes else None


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
    if ctx.node.properties['resource_id']:
        return ctx.node.properties['resource_id']
    return "{0}_{1}_{2}".format(type_name, ctx.deployment.id, ctx.instance.id)


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


def _get_resource_by_name_or_id_from_ctx(ctx, name_field_name, openstack_type,
                                         sugared_client):
    resource_id = ctx.node.properties['resource_id']
    if not resource_id:
        raise NonRecoverableError(
            "Can't set '{0}' to True without supplying a value for "
            "'resource_id'".format(USE_EXTERNAL_RESOURCE_PROPERTY))

    return get_resource_by_name_or_id(resource_id, openstack_type,
                                      sugared_client, True, name_field_name)


def get_resource_by_name_or_id(
        resource_id, openstack_type, sugared_client,
        raise_if_not_found=True, name_field_name='name'):

    # search for resource by name (or name-equivalent field)
    search_param = {name_field_name: resource_id}
    resource = sugared_client.cosmo_get_if_exists(openstack_type,
                                                  **search_param)
    if not resource:
        # fallback - search for resource by id
        resource = sugared_client.cosmo_get_if_exists(
            openstack_type, id=resource_id)

    if not resource and raise_if_not_found:
        raise NonRecoverableError(
            "Couldn't find a resource of type {0} with the name or id {1}"
            .format(openstack_type, resource_id))

    return resource


def use_external_resource(ctx, sugared_client, openstack_type,
                          name_field_name='name'):
    if not is_external_resource(ctx):
        return None

    resource = _get_resource_by_name_or_id_from_ctx(
        ctx, name_field_name, openstack_type, sugared_client)

    ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY] = \
        sugared_client.get_id_from_resource(resource)
    ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY] = openstack_type

    from openstack_plugin_common.floatingip import FLOATINGIP_OPENSTACK_TYPE
    # store openstack name runtime property, unless it's a floating IP type,
    # in which case the ip will be stored in the runtime properties instead.
    if openstack_type != FLOATINGIP_OPENSTACK_TYPE:
        ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY] = \
            sugared_client.get_name_from_resource(resource)

    ctx.logger.info('Using external resource {0}: {1}'.format(
        openstack_type, ctx.node.properties['resource_id']))
    return resource


def validate_resource(ctx, sugared_client, openstack_type,
                      name_field_name='name'):
    ctx.logger.debug('validating resource {0} (node {1})'.format(
        openstack_type, ctx.node.id))

    openstack_type_plural = sugared_client.cosmo_plural(openstack_type)
    if is_external_resource(ctx):
        # validate the resource truly exists
        try:
            _get_resource_by_name_or_id_from_ctx(
                ctx, name_field_name, openstack_type, sugared_client)
            ctx.logger.debug('OK: {0} {1} found in pool'.format(
                openstack_type, ctx.node.properties['resource_id']))
        except NonRecoverableError as e:
            ctx.logger.error('VALIDATION ERROR: ' + str(e))
            resource_list = list(sugared_client.cosmo_list(openstack_type))
            if resource_list:
                ctx.logger.info('list of existing {0}: '.format(
                    openstack_type_plural))
                for resource in resource_list:
                    ctx.logger.info('    {0:>10} - {1}'.format(
                        sugared_client.get_id_from_resource(resource),
                        sugared_client.get_name_from_resource(resource)))
            else:
                ctx.logger.info('there are no existing {0}'.format(
                    openstack_type_plural))
            raise
    else:
        if isinstance(sugared_client, NovaClientWithSugar):
            # not checking quota for Nova resources due to a bug in Nova client
            return

        # validate available quota for provisioning the resource
        resource_list = list(sugared_client.cosmo_list(openstack_type))
        resource_amount = len(resource_list)

        resource_quota = sugared_client.get_quota(openstack_type)
        if resource_amount < resource_quota:
            ctx.logger.debug(
                'OK: {0} (node {1}) can be created. provisioned {2}: {3}, '
                'quota: {4}'
                .format(openstack_type, ctx.node.id, openstack_type_plural,
                        resource_amount, resource_quota))
        else:
            err = ('{0} (node {1}) cannot be created due to quota limitations.'
                   ' provisioned {2}: {3}, quota: {4}'
                   .format(openstack_type, ctx.node.id, openstack_type_plural,
                           resource_amount, resource_quota))
            ctx.logger.error('VALIDATION ERROR:' + err)
            raise NonRecoverableError(err)


def delete_resource_and_runtime_properties(ctx, sugared_client,
                                           runtime_properties_keys):
    node_openstack_type = ctx.instance.runtime_properties[
        OPENSTACK_TYPE_PROPERTY]
    if not is_external_resource(ctx):
        ctx.logger.info('deleting {0}'.format(node_openstack_type))
        sugared_client.cosmo_delete_resource(
            node_openstack_type,
            ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY])
    else:
        ctx.logger.info('not deleting {0} since an external {0} is '
                        'being used'.format(node_openstack_type))

    delete_runtime_properties(ctx, runtime_properties_keys)


def is_external_resource(ctx):
    return is_external_resource_by_properties(ctx.node.properties)


def is_external_relationship(ctx):
    return is_external_resource_by_properties(ctx.source.node.properties) and \
        is_external_resource_by_properties(ctx.target.node.properties)


def is_external_resource_by_properties(properties):
    return USE_EXTERNAL_RESOURCE_PROPERTY in properties and \
        properties[USE_EXTERNAL_RESOURCE_PROPERTY]


def delete_runtime_properties(ctx, runtime_properties_keys):
    for runtime_prop_key in runtime_properties_keys:
        if runtime_prop_key in ctx.instance.runtime_properties:
            del ctx.instance.runtime_properties[runtime_prop_key]


def validate_ip_or_range_syntax(ctx, address, is_range=True):
    range_suffix = ' range' if is_range else ''
    ctx.logger.debug('checking whether {0} is a valid address{1}...'
                     .format(address, range_suffix))
    try:
        IP(address)
        ctx.logger.debug('OK:'
                         '{0} is a valid address{1}.'.format(address,
                                                             range_suffix))
    except ValueError as e:
        err = ('{0} is not a valid address{1}; {2}'.format(
            address, range_suffix, e.message))
        ctx.logger.error('VALIDATION ERROR:' + err)
        raise NonRecoverableError(err)


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
        take_env_var_if_exists('region', 'OS_REGION_NAME')
        take_env_var_if_exists('neutron_url', 'OS_URL')
        take_env_var_if_exists('nova_url', 'NOVACLIENT_BYPASS_URL')

        return cfg

    @staticmethod
    def update_config(overridden_cfg, overriding_cfg):
        """ this method is like dict.update() only that it doesn't override
        with (or set new) empty values (e.g. empty string) """
        for k, v in overriding_cfg.iteritems():
            if v:
                overridden_cfg[k] = v


class OpenStackClient(object):

    REQUIRED_CONFIG_PARAMS = \
        ['username', 'password', 'tenant_name', 'auth_url']

    def get(self, config=None, *args, **kw):
        cfg = Config().get()
        if config:
            Config.update_config(cfg, config)

        self._validate_config(cfg)
        ret = self.connect(cfg, *args, **kw)
        ret.format = 'json'
        return ret

    def _validate_config(self, cfg):
        missing_config_params = self._get_missing_config_params(cfg)
        if missing_config_params:
            self._raise_missing_config_params_error(missing_config_params)

    def _get_missing_config_params(self, cfg):
        missing_config_params = \
            [param for param in self.REQUIRED_CONFIG_PARAMS if param not in
             cfg or not cfg[param]]
        return missing_config_params

    def _raise_missing_config_params_error(self, missing_config_params):
        raise NonRecoverableError(
            "Missing Openstack configuration parameters: {0}; "
            "Expected to find parameters either as environment "
            "variables, in a JSON file (at either a path which is "
            "set under the environment variable {1} or at the "
            "default location {2}), or as nested properties under "
            "a 'openstack_config' property".format(
                ', '.join(missing_config_params),
                Config.OPENSTACK_CONFIG_PATH_ENV_VAR,
                Config.OPENSTACK_CONFIG_PATH_DEFAULT_PATH))


# Clients procurers
class KeystoneClient(OpenStackClient):

    def connect(self, cfg):
        client_kwargs = {field: cfg[field] for field in
                         self.REQUIRED_CONFIG_PARAMS}

        client_kwargs.update(
            cfg.get('custom_configuration', {}).get('keystone_client', {}))

        return KeystoneClientWithSugar(**client_kwargs)


class NovaClient(OpenStackClient):

    def connect(self, cfg):
        # note: 'region_name' is required regardless of whether 'bypass_url'
        # is used or not
        client_kwargs = dict(
            username=cfg['username'],
            api_key=cfg['password'],
            project_id=cfg['tenant_name'],
            auth_url=cfg['auth_url'],
            region_name=cfg.get('region', ''),
            http_log_debug=False
        )

        if cfg.get('nova_url'):
            client_kwargs['bypass_url'] = cfg['nova_url']

        client_kwargs.update(
            cfg.get('custom_configuration', {}).get('nova_client', {}))

        return NovaClientWithSugar(**client_kwargs)


class CinderClient(OpenStackClient):

    def connect(self, cfg):
        client_kwargs = dict(
            username=cfg['username'],
            api_key=cfg['password'],
            project_id=cfg['tenant_name'],
            auth_url=cfg['auth_url'],
            region_name=cfg.get('region', '')
        )

        client_kwargs.update(
            cfg.get('custom_configuration', {}).get('cinder_client', {}))

        return CinderClientWithSugar(**client_kwargs)


class NeutronClient(OpenStackClient):

    def connect(self, cfg):
        client_kwargs = dict(
            username=cfg['username'],
            password=cfg['password'],
            tenant_name=cfg['tenant_name'],
            auth_url=cfg['auth_url'],
        )

        if cfg.get('neutron_url'):
            client_kwargs['endpoint_url'] = cfg['neutron_url']
        else:
            client_kwargs['region_name'] = cfg.get('region', '')

        client_kwargs.update(
            cfg.get('custom_configuration', {}).get('neutron_client', {}))

        return NeutronClientWithSugar(**client_kwargs)


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
        _put_client_in_kw('neutron_client', NeutronClient, kw)

        try:
            return f(*args, **kw)
        except neutron_exceptions.NeutronClientException, e:
            if e.status_code in _non_recoverable_error_codes:
                _re_raise(e, recoverable=False, status_code=e.status_code)
            else:
                raise
    return wrapper


def with_nova_client(f):
    @wraps(f)
    def wrapper(*args, **kw):
        _put_client_in_kw('nova_client', NovaClient, kw)

        try:
            return f(*args, **kw)
        except nova_exceptions.OverLimit, e:
            _re_raise(e, recoverable=True, retry_after=e.retry_after)
        except nova_exceptions.ClientException, e:
            if e.code in _non_recoverable_error_codes:
                _re_raise(e, recoverable=False, status_code=e.code)
            else:
                raise
    return wrapper


def with_cinder_client(f):
    @wraps(f)
    def wrapper(*args, **kw):
        _put_client_in_kw('cinder_client', CinderClient, kw)

        try:
            return f(*args, **kw)
        except cinder_exceptions.ClientException, e:
            if e.code in _non_recoverable_error_codes:
                _re_raise(e, recoverable=False, status_code=e.code)
            else:
                raise
    return wrapper


def with_keystone_client(f):
    @wraps(f)
    def wrapper(*args, **kw):
        _put_client_in_kw('keystone_client', KeystoneClient, kw)

        try:
            return f(*args, **kw)
        except keystone_exceptions.HTTPError, e:
            if e.http_status in _non_recoverable_error_codes:
                _re_raise(e, recoverable=False, status_code=e.http_status)
            else:
                raise
        except keystone_exceptions.ClientException, e:
            _re_raise(e, recoverable=False)
    return wrapper


        return f(*args, **kw)

    return wrapper


def _put_client_in_kw(client_name, client_class, kw):
    if client_name in kw:
        return

    ctx = _find_context_in_kw(kw)
    if ctx.type == context.NODE_INSTANCE:
        config = ctx.node.properties.get('openstack_config')
    elif ctx.type == context.RELATIONSHIP_INSTANCE:
        config = ctx.source.node.properties.get('openstack_config')
        if not config:
            config = ctx.target.node.properties.get('openstack_config')
    else:
        config = None
    kw[client_name] = client_class().get(config=config)


_non_recoverable_error_codes = [400, 401, 403, 404, 409]


def _re_raise(e, recoverable, retry_after=None, status_code=None):
    exc_type, exc, traceback = sys.exc_info()
    message = e.message
    if status_code is not None:
        message = '{0} [status_code={1}]'.format(message, status_code)
    if recoverable:
        if retry_after == 0:
            retry_after = None
        raise RecoverableError(
            message=message,
            retry_after=retry_after), None, traceback
    else:
        raise NonRecoverableError(message), None, traceback


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
        obj_type_plural = self._get_nova_field_name_for_type(obj_type_single)
        for obj in getattr(self, obj_type_plural).findall(**kw):
            yield obj

    def cosmo_delete_resource(self, obj_type_single, obj_id):
        obj_type_plural = self._get_nova_field_name_for_type(obj_type_single)
        getattr(self, obj_type_plural).delete(obj_id)

    def get_id_from_resource(self, resource):
        return resource.id

    def get_name_from_resource(self, resource):
        return resource.name

    def get_quota(self, obj_type_single):
        raise RuntimeError(
            'Retrieving quotas from Nova service is currently unsupported '
            'due to a bug in Nova python client')

        # we're already authenticated, but the following call will make
        # 'service_catalog' available under 'client', through which we can
        # extract the tenant_id (Note that self.client.tenant_id might be
        # None if project_id (AKA tenant_name) was used instead; However the
        # actual tenant_id must be used to retrieve the quotas)
        self.client.authenticate()
        tenant_id = self.client.service_catalog.get_tenant_id()
        quotas = self.quotas.get(tenant_id)
        return getattr(quotas, self.cosmo_plural(obj_type_single))

    def _get_nova_field_name_for_type(self, obj_type_single):
        from openstack_plugin_common.floatingip import \
            FLOATINGIP_OPENSTACK_TYPE
        if obj_type_single == FLOATINGIP_OPENSTACK_TYPE:
            # since we use the same 'openstack type' property value for both
            # neutron and nova floating-ips, this adjustment must be made
            # for nova client, as fields names differ between the two clients
            obj_type_single = 'floating_ip'
        return self.cosmo_plural(obj_type_single)


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

    def get_quota(self, obj_type_single):
        tenant_id = self.get_quotas_tenant()['tenant']['tenant_id']
        quotas = self.show_quota(tenant_id)['quota']
        return quotas[obj_type_single]

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


class CinderClientWithSugar(cinder_client.Client, ClientWithSugar):

    def cosmo_list(self, obj_type_single, **kw):
        obj_type_plural = self.cosmo_plural(obj_type_single)
        for obj in getattr(self, obj_type_plural).findall(**kw):
            yield obj

    def cosmo_delete_resource(self, obj_type_single, obj_id):
        obj_type_plural = self.cosmo_plural(obj_type_single)
        getattr(self, obj_type_plural).delete(obj_id)

    def get_id_from_resource(self, resource):
        return resource.id

    def get_name_from_resource(self, resource):
        return resource.display_name

    def get_quota(self, obj_type_single):
        # we're already authenticated, but the following call will make
        # 'service_catalog' available under 'client', through which we can
        # extract the tenant_id (Note that self.client.tenant_id might be
        # None if project_id (AKA tenant_name) was used instead; However the
        # actual tenant_id must be used to retrieve the quotas)
        self.client.authenticate()
        tenant_id = self.client.service_catalog.get_token()['tenant_id']
        quotas = self.quotas.get(tenant_id)
        return getattr(quotas, self.cosmo_plural(obj_type_single))


class KeystoneClientWithSugar(keystone_client.Client, ClientWithSugar):
    # keystone does not have resource quota
    KEYSTONE_INFINITE_RESOURCE_QUOTA = 10**9

    def cosmo_list(self, obj_type_single, **kw):
        obj_type_plural = self.cosmo_plural(obj_type_single)
        for obj in getattr(self, obj_type_plural).findall(**kw):
            yield obj

    def cosmo_delete_resource(self, obj_type_single, obj_id):
        obj_type_plural = self.cosmo_plural(obj_type_single)
        getattr(self, obj_type_plural).delete(obj_id)

    def get_id_from_resource(self, resource):
        return resource.id

    def get_name_from_resource(self, resource):
        return resource.name

    def get_quota(self, obj_type_single):
        return self.KEYSTONE_INFINITE_RESOURCE_QUOTA
