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

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from openstack_plugin_common import (
    provider,
    transform_resource_name,
    get_resource_id,
    with_neutron_client,
    use_external_resource,
    is_external_relationship,
    delete_resource_and_runtime_properties,
    validate_resource,
    COMMON_RUNTIME_PROPERTIES_KEYS,
    OPENSTACK_ID_PROPERTY,
    OPENSTACK_TYPE_PROPERTY,
    OPENSTACK_NAME_PROPERTY
)

ROUTER_OPENSTACK_TYPE = 'router'

# Runtime properties
RUNTIME_PROPERTIES_KEYS = COMMON_RUNTIME_PROPERTIES_KEYS


@operation
@with_neutron_client
def create(neutron_client, **kwargs):
    """Create a router.
    Optional relationship is to gateway network.
    Also supports `router.external_gateway_info.network_name`,
    which is translated to `router.external_gateway_info.network_id`.
    """

    if use_external_resource(ctx, neutron_client, ROUTER_OPENSTACK_TYPE):
        return

    network_id_set = False

    provider_context = provider(ctx)

    ctx.logger.debug('router.create(): kwargs={0}'.format(kwargs))
    router = {
        'name': get_resource_id(ctx, ROUTER_OPENSTACK_TYPE),
    }
    router.update(ctx.node.properties['router'])
    transform_resource_name(ctx, router)

    # Probably will not be used. External network
    # is usually provisioned externally.
    # TODO: remove this or modify - it's unreasonable to look for
    # OPENSTACK_ID_PROPERTY in capabilities as it can be of any connected
    # node. If the usage of capabilities here remains, need to add
    # validation in the 'use_external_resource' (before returning) that the
    # network used is the one connected to the router.
    if OPENSTACK_ID_PROPERTY in ctx.capabilities:
        if 'external_gateway_info' not in router:
            router['external_gateway_info'] = {
                'enable_snat': True
            }
        router['external_gateway_info'][
            'network_id'] = ctx.capabilities[OPENSTACK_ID_PROPERTY]
        network_id_set = True

    # Sugar: external_gateway_info.network_name ->
    # external_gateway_info.network_id

    if 'external_gateway_info' in router:
        egi = router['external_gateway_info']
        if 'network_name' in egi:
            egi['network_id'] = neutron_client.cosmo_get_named(
                'network', egi['network_name'])['id']
            del egi['network_name']
            network_id_set = True

    if not network_id_set:
        router['external_gateway_info'] = router.get('external_gateway_info',
                                                     {})
        ext_network = provider_context.ext_network
        if ext_network:
            router['external_gateway_info']['network_id'] = ext_network['id']
            network_id_set = True

    if not network_id_set:
        raise NonRecoverableError('Missing network name or network')

    r = neutron_client.create_router({'router': router})['router']

    ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY] = r['id']
    ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY] =\
        ROUTER_OPENSTACK_TYPE
    ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY] = r['name']


@operation
@with_neutron_client
def connect_subnet(neutron_client, **kwargs):
    router_id = ctx.target.instance.runtime_properties[OPENSTACK_ID_PROPERTY]
    subnet_id = ctx.source.instance.runtime_properties[OPENSTACK_ID_PROPERTY]

    if is_external_relationship(ctx):
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


@operation
@with_neutron_client
def disconnect_subnet(neutron_client, **kwargs):
    if is_external_relationship(ctx):
        ctx.logger.info('Not connecting subnet and router since external '
                        'subnet and router are being used')
        return

    neutron_client.remove_interface_router(
        ctx.target.instance.runtime_properties[OPENSTACK_ID_PROPERTY], {
            'subnet_id': ctx.source.instance.runtime_properties[
                OPENSTACK_ID_PROPERTY]
        }
    )


@operation
@with_neutron_client
def delete(neutron_client, **kwargs):
    delete_resource_and_runtime_properties(ctx, neutron_client,
                                           RUNTIME_PROPERTIES_KEYS)


@operation
@with_neutron_client
def creation_validation(neutron_client, **kwargs):
    validate_resource(ctx, neutron_client, ROUTER_OPENSTACK_TYPE)
