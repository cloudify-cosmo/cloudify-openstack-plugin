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
    with_neutron_client,
)

# Runtime properties
OPENSTACK_ID_PROPERTY = 'external_id'  # router's openstack id
RUNTIME_PROPERTIES_KEYS = [OPENSTACK_ID_PROPERTY]


@operation
@with_neutron_client
def create(neutron_client, **kwargs):
    """ Create a router.
    Optional relationship is to gateway network.
    Also supports `router.external_gateway_info.network_name`,
    which is translated to `router.external_gateway_info.network_id`.
    """

    network_id_set = False

    provider_context = provider()

    ctx.logger.debug('router.create(): kwargs={0}'.format(kwargs))
    router = {
        'name': ctx.node_id,
    }
    router.update(ctx.properties['router'])
    transform_resource_name(router)

    # Probably will not be used. External network
    # is usually provisioned externally.
    if 'external_id' in ctx.capabilities:
        if 'external_gateway_info' not in router:
            router['external_gateway_info'] = {
                'enable_snat': True
            }
        router['external_gateway_info'][
            'network_id'] = ctx.capabilities['external_id']
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

    ctx.runtime_properties[OPENSTACK_ID_PROPERTY] = r['id']


@operation
@with_neutron_client
def connect_subnet(neutron_client, **kwargs):
    neutron_client.add_interface_router(
        ctx.runtime_properties[OPENSTACK_ID_PROPERTY],
        {'subnet_id': ctx.related.runtime_properties['external_id']}
    )


@operation
@with_neutron_client
def disconnect_subnet(neutron_client, **kwargs):
    neutron_client.remove_interface_router(
        ctx.runtime_properties[OPENSTACK_ID_PROPERTY],
        {'subnet_id': ctx.related.runtime_properties['external_id']}
    )


@operation
@with_neutron_client
def delete(neutron_client, **kwargs):
    neutron_client.delete_router(ctx.runtime_properties[OPENSTACK_ID_PROPERTY])

    for runtime_prop_key in RUNTIME_PROPERTIES_KEYS:
        del ctx.runtime_properties[runtime_prop_key]