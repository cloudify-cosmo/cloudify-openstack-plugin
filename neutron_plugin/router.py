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

import warnings

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError
try:
    from cloudify.context import RELATIONSHIP_INSTANCE
except ImportError:
    from cloudify.constants import (
        RELATIONSHIP_INSTANCE,
    )

from openstack_plugin_common import (
    provider,
    get_openstack_id,
    get_openstack_type,
    with_neutron_client,
    use_external_resource,
    is_external_relationship,
    is_external_relationship_not_conditionally_created,
    is_external_resource_not_conditionally_created,
    delete_runtime_properties,
    get_relationships_by_relationship_type,
    get_openstack_ids_of_connected_nodes_by_openstack_type,
    delete_resource_and_runtime_properties,
    get_resource_by_name_or_id,
    validate_resource,
    create_object_dict,
    set_neutron_runtime_properties,
    add_list_to_runtime_properties,
    COMMON_RUNTIME_PROPERTIES_KEYS,
    OPENSTACK_TYPE_PROPERTY,
    OPENSTACK_ID_PROPERTY,
    with_resume_operation
)

from neutron_plugin.network import NETWORK_OPENSTACK_TYPE
from neutronclient.common.exceptions import NeutronClientException

ROUTER_OPENSTACK_TYPE = 'router'
ROUTES_OPENSTACK_TYPE = 'routes'
ROUTES_OPENSTACK_NODE_TYPE = 'cloudify.openstack.nodes.Routes'
ROUTES_OPENSTACK_RELATIONSHIP = 'cloudify.openstack.route_connected_to_router'

# Runtime properties
RUNTIME_PROPERTIES_KEYS = COMMON_RUNTIME_PROPERTIES_KEYS


def _update_router_routes(neutron_client, args, **kwargs):

    from copy import deepcopy

    def dict_merge(a, b):
        if isinstance(a, list) and isinstance(b, list):
            a.extend(b)
            return a
        if not isinstance(b, dict):
            return b
        result = deepcopy(a)
        for k, v in b.iteritems():
            if k in result:
                ctx.logger.info('Match {0}'.format(k))
                result[k] = dict_merge(result[k], v)
                ctx.logger.info('Match Routes {0}'.format(k))
        return result

    # Find out if the update script is being called
    # from a relationship or a node operation.
    router = _get_router_from_relationship(neutron_client)

    router_id = router[ROUTER_OPENSTACK_TYPE].pop('id')
    new_router = {ROUTER_OPENSTACK_TYPE: {}}
    for key, value in args.items():
        new_router['router'][key] = value

    for ro_attribute in ['status', 'tenant_id']:
        try:
            del router[ROUTER_OPENSTACK_TYPE][ro_attribute]
        except KeyError:
            pass

    new_router = dict_merge(new_router, router)
    return neutron_client.update_router(router_id, new_router)


@operation(resumable=True)
@with_resume_operation
@with_neutron_client
def create(neutron_client, args, **kwargs):

    if use_external_resource(ctx, neutron_client, ROUTER_OPENSTACK_TYPE):
        try:
            ext_net_id_by_rel = _get_connected_ext_net_id(neutron_client)

            if ext_net_id_by_rel:
                router_id = get_openstack_id(ctx)

                router = neutron_client.show_router(router_id)['router']
                if not (router['external_gateway_info'] and 'network_id' in
                        router['external_gateway_info'] and
                        router['external_gateway_info']['network_id'] ==
                        ext_net_id_by_rel):
                    raise NonRecoverableError(
                        'Expected external resources router {0} and '
                        'external network {1} to be connected'.format(
                            router_id, ext_net_id_by_rel))
            return
        except Exception:
            delete_runtime_properties(ctx, RUNTIME_PROPERTIES_KEYS)
            raise

    router = create_object_dict(ctx, ROUTER_OPENSTACK_TYPE, args, {})
    ctx.logger.info('router: {0}'.format(router))

    _handle_external_network_config(router, neutron_client)

    r = neutron_client.create_router(
        {ROUTER_OPENSTACK_TYPE: router})[ROUTER_OPENSTACK_TYPE]

    set_neutron_runtime_properties(ctx, r, ROUTER_OPENSTACK_TYPE)


@operation(resumable=True)
@with_resume_operation
@with_neutron_client
def update(neutron_client, args, **kwargs):
    if not args:
        raise NonRecoverableError(
            'args must be provided to update '
            'router {0}'.format(kwargs.get('resource_id'))
        )

    router_id = ctx.instance.runtime_properties.get(OPENSTACK_ID_PROPERTY)
    if not router_id:
        raise NonRecoverableError(
            'Router {0} is missing '.format(OPENSTACK_ID_PROPERTY)
        )

    return neutron_client.update_router(router_id, args)


@operation(resumable=True)
@with_resume_operation
@with_neutron_client
def update_routes(neutron_client, args, **kwargs):
    routes = args.get(ROUTES_OPENSTACK_TYPE)
    if not routes:
        raise NonRecoverableError('routes param is required and must be '
                                  'provided when creating static routes !!')
    # Force to pass only the "routes" provided by the node properties
    routes_args = {'routes': routes}

    # This will update the router and add new static routes based on the
    # routes param provided by the "cloudify.openstack.nodes.Routes"
    r = _update_router_routes(neutron_client, routes_args, **kwargs)
    router = r.get(ROUTER_OPENSTACK_TYPE)
    if r and router:
        # If the current context type is a relationship then update the
        # source instance "runtime_properties" otherwise just update the
        # current instance "runtime_properties"
        if ctx.type == RELATIONSHIP_INSTANCE:
            ctx.source.instance.\
                runtime_properties[ROUTES_OPENSTACK_TYPE] = routes
        else:
            ctx.instance.runtime_properties[ROUTES_OPENSTACK_TYPE] = routes
    else:
        raise NonRecoverableError(
            'Failed while trying to retrieve router instance')


@operation(resumable=True)
@with_resume_operation
@with_neutron_client
def add_routes(neutron_client, args, **kwargs):

    # Since routes is part of router and not single API resource for routes
    # "router" resource is used
    router = use_external_resource(ctx, neutron_client, ROUTER_OPENSTACK_TYPE)
    if router:
        # Update routes as part of runtime properties
        ctx.instance.runtime_properties[ROUTES_OPENSTACK_TYPE]\
            = router[ROUTES_OPENSTACK_TYPE]
        # Update type to match it as routes types
        ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY]\
            = ROUTES_OPENSTACK_TYPE
        return

    routes = ctx.node.properties.get(ROUTES_OPENSTACK_TYPE, {})

    if not routes:
        raise NonRecoverableError('routes param is required and must be '
                                  'provided when creating static routes !!')

    # Force to pass only the "routes" provided by the node properties
    routes_args = {'routes': routes}

    # This will update the router and add new static routes based on the
    # routes param provided by the "cloudify.openstack.nodes.Routes"
    r = _update_router_routes(neutron_client, routes_args, **kwargs)
    router = r.get(ROUTER_OPENSTACK_TYPE)
    if r and router:
        set_neutron_runtime_properties(ctx, router, ROUTES_OPENSTACK_TYPE)
        ctx.instance.runtime_properties[ROUTES_OPENSTACK_TYPE] = routes
    else:
        raise NonRecoverableError(
            'Failed while trying to retrieve router instance')


@operation(resumable=True)
@with_resume_operation
@with_neutron_client
def connect_subnet(neutron_client, **kwargs):
    router_id = get_openstack_id(ctx.target)
    subnet_id = get_openstack_id(ctx.source)

    if is_external_relationship_not_conditionally_created(ctx):
        ctx.logger.info('Validating external subnet and router '
                        'are associated')
        for port in neutron_client.list_ports(device_id=router_id)['ports']:
            for fixed_ip in port.get('fixed_ips', []):
                if fixed_ip.get('subnet_id') == subnet_id:
                    return
        raise NonRecoverableError(
            'Expected external resources router {0} and subnet {1} to be '
            'connected'.format(router_id, subnet_id))

    neutron_client.add_interface_router(router_id, {'subnet_id': subnet_id})


@operation(resumable=True)
@with_resume_operation
@with_neutron_client
def disconnect_subnet(neutron_client, **kwargs):
    if is_external_relationship(ctx):
        ctx.logger.info('Not connecting subnet and router since external '
                        'subnet and router are being used')
        return
    node_routes = ctx.source.instance.runtime_properties.get(
        ROUTES_OPENSTACK_TYPE)

    # Only delete routes only if it has "routes" as runtime properties
    if node_routes:
        _delete_routes(neutron_client)

    neutron_client.remove_interface_router(get_openstack_id(ctx.target), {
            'subnet_id': get_openstack_id(ctx.source)
        }
    )


@operation(resumable=True)
@with_resume_operation
@with_neutron_client
def delete(neutron_client, **kwargs):
    delete_resource_and_runtime_properties(ctx, neutron_client,
                                           RUNTIME_PROPERTIES_KEYS)


@operation(resumable=True)
@with_resume_operation
@with_neutron_client
def delete_routes(neutron_client, **kwargs):

    _delete_routes(neutron_client)
    delete_runtime_properties(ctx, RUNTIME_PROPERTIES_KEYS)


@operation(resumable=True)
@with_resume_operation
@with_neutron_client
def list_routers(neutron_client, args, **kwargs):
    router_list = neutron_client.list_routers(**args)
    add_list_to_runtime_properties(ctx,
                                   ROUTER_OPENSTACK_TYPE,
                                   router_list.get('routers', []))


@operation(resumable=True)
@with_resume_operation
@with_neutron_client
def creation_validation(neutron_client, **kwargs):
    validate_resource(ctx, neutron_client, ROUTER_OPENSTACK_TYPE)


def _insert_ext_net_id_to_router_config(ext_net_id, router):
    router['external_gateway_info'] = router.get(
        'external_gateway_info', {})
    router['external_gateway_info']['network_id'] = ext_net_id


def _handle_external_network_config(router, neutron_client):
    # attempting to find an external network for the router to connect to -
    # first by either a network name or id passed in explicitly; then by a
    # network connected by a relationship; with a final optional fallback to an
    # external network set in the Provider-context. Otherwise the router will
    # simply not get connected to an external network

    provider_context = provider(ctx)

    ext_net_id_by_rel = _get_connected_ext_net_id(neutron_client)
    ext_net_by_property = ctx.node.properties['external_network']

    # the following is meant for backwards compatibility with the
    # 'network_name' sugaring
    if 'external_gateway_info' in router and 'network_name' in \
            router['external_gateway_info']:
        warnings.warn(
            'Passing external "network_name" inside the '
            'external_gateway_info key of the "router" property is now '
            'deprecated; Use the "external_network" property instead',
            DeprecationWarning)

        ext_net_by_property = router['external_gateway_info']['network_name']
        del (router['external_gateway_info']['network_name'])

    # need to check if the user explicitly passed network_id in the external
    # gateway configuration as it affects external network behavior by
    # relationship and/or provider context
    if 'external_gateway_info' in router and 'network_id' in \
            router['external_gateway_info']:
        ext_net_by_property = \
            router['external_gateway_info'].get('network_name')

    if ext_net_by_property and ext_net_id_by_rel:
        raise RuntimeError(
            "Router can't have an external network connected by both a "
            'relationship and by a network name/id')

    if ext_net_by_property:
        ext_net_id = get_resource_by_name_or_id(
            ext_net_by_property, NETWORK_OPENSTACK_TYPE, neutron_client)['id']
        _insert_ext_net_id_to_router_config(ext_net_id, router)
    elif ext_net_id_by_rel:
        _insert_ext_net_id_to_router_config(ext_net_id_by_rel, router)
    elif ctx.node.properties['default_to_managers_external_network'] and \
            provider_context.ext_network:
        _insert_ext_net_id_to_router_config(provider_context.ext_network['id'],
                                            router)


def _check_if_network_is_external(neutron_client, network_id):
    return neutron_client.show_network(
        network_id)['network']['router:external']


def _get_connected_ext_net_id(neutron_client):
    ext_net_ids = \
        [net_id
            for net_id in
            get_openstack_ids_of_connected_nodes_by_openstack_type(
                ctx, NETWORK_OPENSTACK_TYPE) if
            _check_if_network_is_external(neutron_client, net_id)]

    if len(ext_net_ids) > 1:
        raise NonRecoverableError(
            'More than one external network is connected to router {0}'
            ' by a relationship; External network IDs: {0}'.format(
                ext_net_ids))

    return ext_net_ids[0] if ext_net_ids else None


def _get_router_from_relationship(neutron_client):
    # Find out if the update script is being called
    # from a relationship or a node operation.

    # Only get the "router_rel" if it is not a relationship instance
    if ctx.type != RELATIONSHIP_INSTANCE:

        router_rel = get_relationships_by_relationship_type(
            ctx, ROUTES_OPENSTACK_RELATIONSHIP)

        if router_rel and ROUTER_OPENSTACK_TYPE in get_openstack_type(
                router_rel[0].target):
            subject = router_rel[0].target
        else:
            subject = ctx

    elif ctx.type == RELATIONSHIP_INSTANCE:
        if ROUTER_OPENSTACK_TYPE in get_openstack_type(ctx.source):
            subject = ctx.source
        elif ROUTER_OPENSTACK_TYPE in get_openstack_type(ctx.target):
            subject = ctx.target
        else:
            raise NonRecoverableError(
                'Neither target nor source is {0}'.format(
                    ROUTER_OPENSTACK_TYPE))

    try:
        router = neutron_client.show_router(get_openstack_id(subject))
    except NeutronClientException as e:
        raise NonRecoverableError('Error: {0}'.format(str(e)))
    if not isinstance(router, dict) or \
            ROUTER_OPENSTACK_TYPE not in router.keys() or \
            'id' not in router['router'].keys():
        raise NonRecoverableError(
            'API returned unexpected structure.: {0}'.format(router))

    return router


def _prepare_delete_routes_request(neutron_client):
    # Empty the "static routes" for the router connected to the routes

    if ctx.type != RELATIONSHIP_INSTANCE:
        node_routes =\
            ctx.instance.runtime_properties.get(ROUTES_OPENSTACK_TYPE)
    else:
        node_routes =\
            ctx.source.instance.runtime_properties.get(ROUTES_OPENSTACK_TYPE)

    if node_routes is None:
        raise NonRecoverableError('Unable to get routes from instance !!')

    router = _get_router_from_relationship(neutron_client)
    routes = router[ROUTER_OPENSTACK_TYPE].get(ROUTES_OPENSTACK_TYPE)

    new_router = {ROUTER_OPENSTACK_TYPE: {}}

    for index, main_route in enumerate(routes):
        for node_route in node_routes:
            if main_route == node_route:
                del routes[index]

    new_router[ROUTER_OPENSTACK_TYPE]['id'] =\
        router[ROUTER_OPENSTACK_TYPE].get('id')
    new_router[ROUTER_OPENSTACK_TYPE]['routes'] = routes
    return new_router


def _delete_routes(neutron_client):
    new_router = _prepare_delete_routes_request(neutron_client)
    if new_router and new_router.get(ROUTER_OPENSTACK_TYPE):
        router_id = new_router[ROUTER_OPENSTACK_TYPE].pop('id')
    else:
        raise NonRecoverableError(
            'Failed while trying to retrieve router instance')

    subject = ctx.source if ctx.type == RELATIONSHIP_INSTANCE else ctx
    if not is_external_resource_not_conditionally_created(subject):
        ctx.logger.info('deleting {0}'.format(ROUTES_OPENSTACK_TYPE))
        neutron_client.update_router(router_id, new_router)
    else:
        ctx.logger.info('not deleting {0} since an external {0} is '
                        'being used'.format(ROUTES_OPENSTACK_TYPE))
