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
    use_external_resource,
    delete_resource_and_runtime_properties,
    validate_resource,
    provider,
    get_openstack_id,
    get_single_connected_node_by_openstack_type,
    add_list_to_runtime_properties,
    is_external_relationship,
    is_external_relationship_not_conditionally_created,
    OPENSTACK_ID_PROPERTY,
    OPENSTACK_TYPE_PROPERTY,
    COMMON_RUNTIME_PROPERTIES_KEYS
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

# Runtime properties
IP_ADDRESS_PROPERTY = 'floating_ip_address'  # the actual ip address
RUNTIME_PROPERTIES_KEYS = COMMON_RUNTIME_PROPERTIES_KEYS + \
    [IP_ADDRESS_PROPERTY]


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

    connected_network = \
        get_single_connected_node_by_openstack_type(
            ctx, NETWORK_OPENSTACK_TYPE, True)

    if connected_network:
        network_from_rel = connected_network.runtime_properties[
            OPENSTACK_ID_PROPERTY]
    else:
        network_from_rel = None

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

    if network_from_rel:
        floatingip['floating_network_id'] = network_from_rel
    elif network_name_provided:
        floatingip['floating_network_id'] = neutron_client.cosmo_get_named(
            'network', floatingip['floating_network_name'])['id']
        del floatingip['floating_network_name']
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
    set_floatingip_runtime_properties(fip)

    ctx.logger.info('Floating IP creation response: {0}'.format(fip))


@operation
@with_neutron_client
def delete(neutron_client, **kwargs):
    delete_resource_and_runtime_properties(ctx, neutron_client,
                                           RUNTIME_PROPERTIES_KEYS)


@with_neutron_client
def list_floatingips(neutron_client, args, **kwargs):
    fip_list = neutron_client.list_floatingips(**args)
    add_list_to_runtime_properties(ctx,
                                   FLOATINGIP_OPENSTACK_TYPE,
                                   fip_list.get('floatingips', []))


@operation
@with_neutron_client
def creation_validation(neutron_client, **kwargs):
    validate_resource(ctx, neutron_client, FLOATINGIP_OPENSTACK_TYPE,
                      'floating_ip_address')


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


def use_external_floatingip(client, ip_field_name, ext_fip_ip_extractor):
    external_fip = use_external_resource(
        ctx, client, FLOATINGIP_OPENSTACK_TYPE, ip_field_name)
    if external_fip:
        ctx.instance.runtime_properties[IP_ADDRESS_PROPERTY] = \
            ext_fip_ip_extractor(external_fip)
        return True

    return False


def set_floatingip_runtime_properties(fip):
    ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY] = fip['id']
    ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY] = \
        FLOATINGIP_OPENSTACK_TYPE
    ctx.instance.runtime_properties[IP_ADDRESS_PROPERTY] = \
        fip['floating_ip_address']


def get_server_floating_ip(neutron_client, server_id):
    floating_ips = neutron_client.list_floatingips()

    floating_ips = floating_ips.get('floatingips')
    if not floating_ips:
        return None

    for floating_ip in floating_ips:
        port_id = floating_ip.get('port_id')
        if not port_id:
            # this floating ip is not attached to any port
            continue

        port = neutron_client.show_port(port_id)['port']
        device_id = port.get('device_id')
        if not device_id:
            # this port is not attached to any server
            continue

        if server_id == device_id:
            return floating_ip
    return None
