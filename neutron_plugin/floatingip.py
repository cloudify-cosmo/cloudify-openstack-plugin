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
    with_neutron_client,
    provider,
    get_openstack_id,
    add_list_to_runtime_properties,
    is_external_relationship,
    is_external_relationship_not_conditionally_created,
    get_openstack_id_of_single_connected_node_by_openstack_type,
)
from openstack_plugin_common.floatingip import (
    use_external_floatingip,
    set_floatingip_runtime_properties,
    delete_floatingip,
    floatingip_creation_validation
)
from network import NETWORK_OPENSTACK_TYPE

FLOATINGIP_OPENSTACK_TYPE = 'floatingip'
FLOATING_NETWORK_ERROR_PREFIX = \
    'Network name must be specified by either a floating_network_name, a ' \
    'floating_network_id, or a relationship to a Network node template '
FLOATING_NETWORK_ERROR_SUFFIX = \
    '(provided: network from relationships={}, floatingip={})'
FLOATING_NETWORK_ERROR_MSG = FLOATING_NETWORK_ERROR_PREFIX +\
                             FLOATING_NETWORK_ERROR_SUFFIX


@operation
@with_neutron_client
def create(neutron_client, args, **kwargs):

    if use_external_floatingip(neutron_client, 'floating_ip_address',
                               lambda ext_fip: ext_fip['floating_ip_address']):
        return

    floatingip = {
        # No defaults
    }
    floatingip.update(ctx.node.properties[FLOATINGIP_OPENSTACK_TYPE], **args)

    # Do we have a relationship with a network?

    network_from_rel = \
        get_openstack_id_of_single_connected_node_by_openstack_type(
            ctx, NETWORK_OPENSTACK_TYPE, True)

    # TODO: Should we check whether this is really an "external" network?

    network_name_provided = 'floating_network_name' in floatingip
    network_id_provided = 'floating_network_id' in floatingip
    provided = [network_name_provided,
                network_id_provided,
                network_from_rel is not None].count(True)

    # At most one is expected.

    if provided > 1:
        raise NonRecoverableError(FLOATING_NETWORK_ERROR_MSG.format(
            network_from_rel, floatingip))

    if network_name_provided:
        floatingip['floating_network_id'] = neutron_client.cosmo_get_named(
            'network', floatingip['floating_network_name'])['id']
        del floatingip['floating_network_name']
    elif network_from_rel:
        floatingip['floating_network_id'] = network_from_rel
    elif not network_id_provided:
        provider_context = provider(ctx)
        ext_network = provider_context.ext_network
        if ext_network:
            floatingip['floating_network_id'] = ext_network['id']
        else:
            raise NonRecoverableError(FLOATING_NETWORK_ERROR_MSG.format(
                None, None))

    fip = neutron_client.create_floatingip(
        {FLOATINGIP_OPENSTACK_TYPE: floatingip})[FLOATINGIP_OPENSTACK_TYPE]
    set_floatingip_runtime_properties(fip['id'], fip['floating_ip_address'])

    ctx.logger.info('Floating IP creation response: {0}'.format(fip))


@operation
@with_neutron_client
def delete(neutron_client, **kwargs):
    delete_floatingip(neutron_client)


@with_neutron_client
def list_floatingips(neutron_client, args, **kwargs):
    fip_list = neutron_client.list_floatingips(**args)
    add_list_to_runtime_properties(ctx,
                                   FLOATINGIP_OPENSTACK_TYPE,
                                   fip_list.get('floatingips', []))


@operation
@with_neutron_client
def creation_validation(neutron_client, **kwargs):
    floatingip_creation_validation(neutron_client, 'floating_ip_address')


@operation
@with_neutron_client
def connect_port(neutron_client, **kwargs):
    if is_external_relationship_not_conditionally_created(ctx):
        return

    port_id = get_openstack_id(ctx.source)
    floating_ip_id = get_openstack_id(ctx.target)
    fip = {'port_id': port_id}
    neutron_client.update_floatingip(
        floating_ip_id, {FLOATINGIP_OPENSTACK_TYPE: fip})


@operation
@with_neutron_client
def disconnect_port(neutron_client, **kwargs):
    if is_external_relationship(ctx):
        ctx.logger.info('Not disassociating floatingip and port since '
                        'external floatingip and port are being used')
        return

    floating_ip_id = get_openstack_id(ctx.target)
    fip = {'port_id': None}
    neutron_client.update_floatingip(floating_ip_id,
                                     {FLOATINGIP_OPENSTACK_TYPE: fip})
