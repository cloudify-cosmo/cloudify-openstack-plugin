# #######
# Copyright (c) 2019 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Third party imports
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError

from IPy import IP

# Local imports
from openstack_sdk.resources.networks import OpenstackPort
from openstack_sdk.resources.compute import OpenstackServer
from openstack_plugin.decorators import (with_openstack_resource,
                                         with_compat_node,
                                         with_multiple_data_sources)
from openstack_plugin.constants import (RESOURCE_ID,
                                        PORT_OPENSTACK_TYPE,
                                        NETWORK_OPENSTACK_TYPE,
                                        SECURITY_GROUP_OPENSTACK_TYPE)
from openstack_plugin.utils import (
    update_runtime_properties,
    reset_dict_empty_keys,
    validate_resource_quota,
    add_resource_list_to_runtime_properties,
    find_openstack_ids_of_connected_nodes_by_openstack_type)


@with_multiple_data_sources()
def _update_network_config(port_config, allow_multiple=False):
    """
    This method will try to update oprt config with network configurations
    using the relationships connected with port node
    :param port_config: The port configuration required in order to
    create the port instance using Openstack API
    :param boolean allow_multiple: This flag to set if it is allowed to have
    networks configuration from multiple resources relationships + node
    properties
    """
    # Get network id from port config
    network_id = port_config.get('network_id')

    # Get the network id from relationship if any
    rel_network_ids = find_openstack_ids_of_connected_nodes_by_openstack_type(
        ctx, NETWORK_OPENSTACK_TYPE)

    rel_network_id = rel_network_ids[0] if rel_network_ids else None
    # Check if network config comes from two sources or not
    if network_id and rel_network_id and not allow_multiple:
        raise NonRecoverableError('Port can\'t both have the '
                                  '"network_id" property and be '
                                  'connected to a network via a '
                                  'relationship at the same time')

    port_config['network_id'] = network_id or rel_network_id


@with_multiple_data_sources()
def _update_security_groups_config(port_config, allow_multiple=False):
    """
    This method will try to update oprt config with securit groups
    configurations using the relationships connected with port node
    :param port_config: The port configuration required in order to
    create the port instance using Openstack API
    :param boolean allow_multiple: This flag to set if it is allowed to have
    security groups configuration from multiple resources relationships + node
    properties
    """

    # Get security groups from port config
    security_groups = port_config.get('security_groups')

    # Get the security groups from relationship if any
    rel_security_groups = \
        find_openstack_ids_of_connected_nodes_by_openstack_type(
            ctx, SECURITY_GROUP_OPENSTACK_TYPE)

    # Check if network config comes from two sources or not
    if rel_security_groups and security_groups and not allow_multiple:
        raise NonRecoverableError('Port can\'t both have the '
                                  '"security_groups" property and be '
                                  'connected to a network via a '
                                  'relationship at the same time')

    port_config['security_groups'] = security_groups or rel_security_groups


def _update_fixed_ips_config(port_config):
    """
    This method will handle updating the fixed ips for port when user
    provide data for fixed ips using resource_config and from "fixed_ip"
    node property
    :param port_config: The port configuration required in order to
    create the port instance using Openstack API
    """
    fixed_ip_prop = ctx.node.properties.get('fixed_ip')
    if not (port_config.get('fixed_ips') or fixed_ip_prop):
        return

    elif not port_config.get('fixed_ips'):
        port_config['fixed_ips'] = []

    if fixed_ip_prop:
        for item in port_config['fixed_ips']:
            if item.get('ip_address') and item['ip_address'] == fixed_ip_prop:
                break
        else:
            port_config['fixed_ips'].append({'ip_address': fixed_ip_prop})


def _update_port_config(port_config):
    """
    This method will try to resolve if there are any nodes connected to the
    port node and try to update the configurations from nodes in order to
    help create port from configurations
    :param port_config: The port configuration required in order to
    create the port instance using Openstack API
    """

    # Update network config for port node
    _update_network_config(port_config)

    # Update network fixed ips config
    _update_fixed_ips_config(port_config)

    # Update security groups config for port node
    _update_security_groups_config(port_config)


def _update_external_port(openstack_resource):
    """
    This method will update external port by attaching new ips to external
    port
    :param openstack_resource: Instance Of OpenstackPort in order to
    use it
    """
    # Get the external port using the resource id provided via port node
    external_port = openstack_resource.get()
    # Check if the current port node has allowed_address_pairs as part of
    # resource_config
    addresses_to_add = openstack_resource.config.get('allowed_address_pairs')
    if addresses_to_add:
        old_addresses = external_port.get('allowed_address_pairs') or []

        # Get the old ips from the each pair
        old_ips = \
            [
                old_address['ip_address']
                for old_address
                in old_addresses if old_address.get('ip_address')
            ]
        # Get the ips need to be added to the external port
        ips_to_add = \
            [
                address_to_add['ip_address']
                for address_to_add
                in addresses_to_add if address_to_add.get('ip_address')
            ]

        # Check if there are a common ips between old ips and the one we
        # should add via node
        common_ips = set(old_ips) & set(ips_to_add)
        if common_ips:
            raise NonRecoverableError(
                'Ips {0} are already assigned to {1}'
                ''.format(common_ips, external_port.id))

        # Update port for allowed paris
        updated_port = openstack_resource.update(
            {'allowed_address_pairs':  addresses_to_add})
        # Update runtime properties
        update_runtime_properties(
            {
                'fixed_ips': updated_port.fixed_ips,
                'mac_address': updated_port.mac_address,
                'allowed_address_pairs': updated_port.allowed_address_pairs,
            }
        )

    # Get the networks from relationships if they are existed
    rel_network_ids = find_openstack_ids_of_connected_nodes_by_openstack_type(
        ctx, NETWORK_OPENSTACK_TYPE)

    rel_network_id = rel_network_ids[0] if rel_network_ids else None
    if rel_network_id:
        port = openstack_resource.get()
        if port['network_id'] != rel_network_id:
            raise NonRecoverableError(
                'Expected external resources port {0} and network {1} '
                'to be connected'.format(port.id, rel_network_id))


def _clean_addresses_from_external_port(openstack_resource):
    """
    This method will clean all updated addresses added to the external port
    while the port node created at install workflow
    :param openstack_resource:
    """
    # Get the external port using the resource id provided via port node
    external_port = openstack_resource.get()
    # Check if the current port node has allowed_address_pairs as part of
    # resource_config
    addresses_to_remove = openstack_resource.config.get(
        'allowed_address_pairs')

    if addresses_to_remove:
        remote_addresses = external_port.allowed_address_pairs or []
        # Get the remote ips from the each pair
        remote_ips = \
            [
                remote_address['ip_address']
                for remote_address
                in remote_addresses if remote_address.get('ip_address')
            ]

        # Get the ips need to be removed to the external port
        ips_to_remove = \
            [
                address_to_remove['ip_address']
                for address_to_remove
                in addresses_to_remove if address_to_remove.get('ip_address')
            ]

        # Check if there are a common ips between old ips and the one we
        # should remove via node
        diff_ips = set(remote_ips) - set(ips_to_remove)
        diff_ips = list(diff_ips) if diff_ips else []
        updated_pairs = []
        for ip_address in diff_ips:
            updated_pairs.append({'ip_address': ip_address})

        # Update port for allowed paris
        openstack_resource.update({'allowed_address_pairs':  updated_pairs})


def _update_port_association(client_config, port_id, device_id=''):
    """
     This method will handle linking & un-linking port to server
    :param client_config: Client configuration in order to call OS API
    :param port_id: Port Id to link/un-link with
    :param device_id: Server Id to attach/detach port from/to
    """
    # Check if the port is provided or not
    if not port_id:
        raise NonRecoverableError(
            'Unable to attach port to device {0},'
            ' `port_id` is missing'.format(
                device_id)
        )
    # Prepare the port instance to attach/detach server from/to the current
    # port
    port_resource = OpenstackPort(client_config=client_config,
                                  logger=ctx.logger)

    # Set port id
    port_resource.resource_id = port_id

    # Update port
    port_resource.update({'device_id': device_id})


def _get_fixed_ips_from_port(port):
    """
    This method will extract ipv4 & ipv6 for from port object
    :param port: Port instance of type `~openstack.network.v2.port.Port`
    :return: Tuple of list contains lists for ipv4 & ipv6
    """
    net_ips = port['fixed_ips'] if port.get('fixed_ips') else []
    ips_v4 = []
    ips_v6 = []
    for net_ip in net_ips:
        if net_ip.get('ip_address'):
            ip_address = net_ip['ip_address']
            try:
                # Lookup all ipv4s
                IP(ip_address, ipversion=4)
                ips_v4.append(ip_address)
            except ValueError:
                # If it is not an ipv4 then collect the ipv6
                IP(ip_address, ipversion=6)
                ips_v6.append(ip_address)
    return ips_v4, ips_v6


def _export_ips_to_port_instance(ips_v4, ips_v6):
    """
    This method will export ips of the current port as runtime properties
    for port node instance to be access later on
    :param ips_v4: List of ip version 4
    :param ips_v6: List of ip version 6
    """
    # Set list of ipv4 for the current nod as runtime properties
    ctx.instance.runtime_properties['ipv4_addresses'] = ips_v4
    # # Set list of ipv6 for the current nod as runtime properties
    ctx.instance.runtime_properties['ipv6_addresses'] = ips_v6

    if len(ips_v4) == 1:
        ctx.instance.runtime_properties['ipv4_address'] = ips_v4[0]
    else:
        ctx.instance.runtime_properties['ipv4_address'] = ''

    if len(ips_v6) == 1:
        ctx.instance.runtime_properties['ipv6_address'] = ips_v6[0]
    else:
        ctx.instance.runtime_properties['ipv6_address'] = ''


@with_compat_node
@with_openstack_resource(
    OpenstackPort,
    existing_resource_handler=_update_external_port)
def create(openstack_resource):
    """
    Create openstack port instance
    :param openstack_resource: instance of openstack port resource
    """
    # Update port config before create port
    _update_port_config(openstack_resource.config)

    # Create port
    created_resource = openstack_resource.create()
    ipv4_list, ipv6_list = _get_fixed_ips_from_port(created_resource)
    fixed_ips = ipv4_list + ipv6_list
    _export_ips_to_port_instance(ipv4_list, ipv6_list)

    # Handle runtime properties
    update_runtime_properties(
        {
            RESOURCE_ID: created_resource.id,
            'fixed_ips': fixed_ips,
            'mac_address': created_resource.mac_address,
            'allowed_address_pairs': created_resource.allowed_address_pairs,
        }
    )


@with_compat_node
@with_openstack_resource(
    OpenstackPort,
    existing_resource_handler=_clean_addresses_from_external_port)
def delete(openstack_resource):
    """
    Delete current openstack port
    :param openstack_resource: instance of openstack port resource
    """
    openstack_resource.delete()


@with_compat_node
@with_openstack_resource(OpenstackPort)
def update(openstack_resource, args):
    """
    Update openstack port by passing args dict that contains the info that
    need to be updated
    :param openstack_resource: instance of openstack port resource
    :param args: dict of information need to be updated
    """
    args = reset_dict_empty_keys(args)
    openstack_resource.update(args)


@with_compat_node
# The attach relationship is linked from source (server) ---> target (port)
# So that the resource being evaluated is OpenstackServer
@with_openstack_resource(OpenstackServer)
def attach(openstack_resource, port_id):
    """
    This method will attach port to device (server)
    :param openstack_resource: Instance of openstack server resource
    :param port_id: Port id to attach device to
    """
    device_id = openstack_resource.resource_id
    # Check if the port is provided or not
    if not port_id:
        raise NonRecoverableError(
            'Unable to attach port to device {0},'
            ' `port_id` is missing'.format(
                device_id)
        )
    # Attach server to server
    _update_port_association(openstack_resource.client_config,
                             port_id,
                             device_id)


@with_compat_node
@with_openstack_resource(OpenstackServer)
def detach(openstack_resource, port_id):
    """
    This method will detach port from device (server)
    :param openstack_resource: Instance of openstack server resource
    :param port_id: Port id to detach device from
    """
    device_id = openstack_resource.resource_id
    # Check if the port is provided or not
    if not port_id:
        raise NonRecoverableError(
            'Unable to attach port to device {0},'
            ' `port_id` is missing'.format(
                device_id)
        )
    # Unlink port connection from server
    # No need to detach floating ip from the port because when delete port
    # with floating ip assigned to port it can removed without any issue
    _update_port_association(openstack_resource.client_config,
                             port_id)


@with_compat_node
@with_openstack_resource(OpenstackServer)
def create_server_interface(openstack_resource, port_id, **_):
    """
    This method will create an interface on a server and perform the
    attachment.
    :param openstack_resource:
    :param port_id:
    :return:
    """
    for interface_attachments in openstack_resource.server_interfaces():
        if port_id in interface_attachments:
            return
    openstack_resource.create_server_interface(
        interface_config={'port_id': port_id})


@with_compat_node
@with_openstack_resource(OpenstackServer)
def delete_server_interface(openstack_resource, port_id, **_):
    """
    This method will delete an interface on a server and perform the
    attachment.
    :param openstack_resource:
    :param port_id:
    :return:
    """
    for interface_attachments in openstack_resource.server_interfaces():
        if interface_attachments.id == port_id:
            openstack_resource.delete_server_interface(port_id)
            _update_port_association(openstack_resource.client_config,
                                     port_id)


@with_compat_node
@with_openstack_resource(OpenstackPort)
def attach_to_server(openstack_resource, device_id):
    """
    This method will attach port to device (server)
    :param openstack_resource: Instance of openstack server resource
    :param device_id: Device id to attach port to
    """
    port_id = openstack_resource.resource_id
    # Check if the port is provided or not
    if not device_id:
        raise NonRecoverableError(
            'Unable to attach port to device {0},'
            ' `device_id` is missing'.format(
                device_id)
        )
    # Attach port to server
    _update_port_association(openstack_resource.client_config,
                             port_id,
                             device_id)


@with_compat_node
@with_openstack_resource(OpenstackPort)
def detach_from_server(openstack_resource, device_id):
    """
    This method will detach port from device (server)
    :param openstack_resource: Instance of openstack server resource
    :param device_id: Device id to detach port from
    """
    port_id = openstack_resource.resource_id
    # Check if the port is provided or not
    if not device_id:
        raise NonRecoverableError(
            'Unable to attach port to device {0},'
            ' `device_id` is missing'.format(
                device_id)
        )
    # Unlink port connection from server
    # No need to detach floating ip from the port because when delete port
    # with floating ip assigned to port it can removed without any issue
    _update_port_association(openstack_resource.client_config,
                             port_id)


@with_compat_node
@with_openstack_resource(OpenstackPort)
def list_ports(openstack_resource, query=None):
    """
    List openstack ports based on filters applied
    :param openstack_resource: Instance of current openstack port
    :param kwargs query: Optional query parameters to be sent to limit
            the ports being returned.
    """
    ports = openstack_resource.list(query)
    add_resource_list_to_runtime_properties(PORT_OPENSTACK_TYPE, ports)


@with_compat_node
@with_openstack_resource(OpenstackPort)
def creation_validation(openstack_resource):
    """
    This method is to check if we can create port resource in openstack
    :param openstack_resource: Instance of current openstack port
    """
    validate_resource_quota(openstack_resource, PORT_OPENSTACK_TYPE)
    ctx.logger.debug('OK: port configuration is valid')
