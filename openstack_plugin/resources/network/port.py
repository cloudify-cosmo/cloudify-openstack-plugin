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

# Local imports
from openstack_sdk.resources.networks import OpenstackPort

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
    find_openstack_ids_of_connected_nodes_by_openstack_type,
    cleanup_runtime_properties)


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

    # Handle runtime properties
    update_runtime_properties(
        {
            RESOURCE_ID: created_resource.id,
            'fixed_ips': created_resource.fixed_ips,
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
    if not ctx.instance.runtime_properties.get(RESOURCE_ID):
        ctx.logger.info('Port is already uninitialized.')
        return
    openstack_resource.delete()
    cleanup_runtime_properties(ctx, [
        RESOURCE_ID, 'fixed_ips', 'mac_address', 'allowed_address_pairs'
    ])


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
