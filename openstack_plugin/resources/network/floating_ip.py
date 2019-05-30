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
from cloudify.exceptions import (RecoverableError, NonRecoverableError)

# Local imports
from openstack_sdk.resources.networks import (OpenstackFloatingIP,
                                              OpenstackNetwork)

from openstack_plugin.decorators import (with_openstack_resource,
                                         with_compat_node,
                                         with_multiple_data_sources)

from openstack_plugin.constants import (RESOURCE_ID,
                                        FLOATING_IP_OPENSTACK_TYPE,
                                        NETWORK_OPENSTACK_TYPE,
                                        SUBNET_OPENSTACK_TYPE,
                                        PORT_OPENSTACK_TYPE)
from openstack_plugin.utils import (
    reset_dict_empty_keys,
    validate_resource_quota,
    add_resource_list_to_runtime_properties,
    find_openstack_ids_of_connected_nodes_by_openstack_type)


def use_external_floating_ip(openstack_resource):
    """
    This method will allow floating ip reallocation whenever
    use_external_resource is set to "True" and "allow_reallocation" is enabled
    :param openstack_resource: Instance Of OpenstackFloatingIP in order to
    use it
    """

    remote_resource = openstack_resource.get()
    status = remote_resource.status
    floating_ip = remote_resource.floating_ip_address
    if not ctx.node.properties['allow_reallocation'] and status == 'ACTIVE':
        raise RecoverableError(
            'Floating IP address {0} is already associated'.format(floating_ip)
        )
    # Set the floating ip address as runtime property if "allow_reallocation"
    # is set to "True"
    ctx.instance.runtime_properties['floating_ip_address'] = floating_ip


def _get_floating_network_id_from_relationship(resource_type):
    """
    This method will find if floating ip node is connected to the following
    resource types:
     - Port
     - Network
     - Subnet
    Using relationship and will raise error if it is connected to
    multiple resources
    :param str resource_type: Instance of openstack floating ip
    resource
    :return str floating_network_id: Floating network id
    """
    # Get the network id from relationship if it is existed
    resource_ids = find_openstack_ids_of_connected_nodes_by_openstack_type(
        ctx, resource_type)
    # Check if floating ip is connected to multiple resources
    if len(resource_ids) > 1:
        raise NonRecoverableError(
            'Cannot attach floating ip to multiple '
            '{0}s {1}'.format(','.join(resource_ids), resource_type))

    return resource_ids[0] if resource_ids else None


@with_multiple_data_sources()
def _update_floating_ip_port(floating_ip_resource, allow_multiple=False):
    """
    This method will try to update floating ip config with port
    configurations using the relationships connected with floating ip node
    :param dict floating_ip_resource: Instance of openstack floating ip
    resource
    :param boolean allow_multiple: This flag to set if it is allowed to have
    ports configuration from multiple resources relationships + node
    properties
    """

    # Check to see if the floating port id is provided on the floating ip
    # config properties
    floating_ip_config = floating_ip_resource.config
    port_id = floating_ip_config.get('port_id')

    # Get the floating port id from relationship if it is existed
    rel_port_id = \
        _get_floating_network_id_from_relationship(PORT_OPENSTACK_TYPE)
    if port_id and rel_port_id and not allow_multiple:
        raise NonRecoverableError('Floating IP can\'t both have the '
                                  '"port_id" property and be '
                                  'connected to a port via a '
                                  'relationship at the same time')

    if port_id or rel_port_id:
        floating_ip_config['port_id'] = rel_port_id or port_id


@with_multiple_data_sources()
def _update_floating_ip_subnet(floating_ip_resource, allow_multiple=False):
    """
    This method will try to update floating ip config with subnet
    configurations using the relationships connected with floating ip node
    :param dict floating_ip_resource: Instance of openstack floating ip
    resource
    :param boolean allow_multiple: This flag to set if it is allowed to have
    subnets configuration from multiple resources relationships + node
    properties
    """
    # Check to see if the floating port id is provided on the floating ip
    # config properties
    floating_ip_config = floating_ip_resource.config
    subnet_id = floating_ip_config.get('subnet_id')

    # Get the floating subnet id from relationship if it is existed
    rel_subnet_id = \
        _get_floating_network_id_from_relationship(SUBNET_OPENSTACK_TYPE)
    if subnet_id and rel_subnet_id and not allow_multiple:
        raise NonRecoverableError('Floating IP can\'t both have the '
                                  '"subnet_id" property and be '
                                  'connected to a subnet via a '
                                  'relationship at the same time')

    if subnet_id or rel_subnet_id:
        floating_ip_config['subnet_id'] = rel_subnet_id or subnet_id


@with_multiple_data_sources()
def _update_floating_ip_network(floating_ip_resource, allow_multiple=False):
    """
    This method will try to update floating ip config with network
    configurations using the relationships connected with floating ip node
    :param dict floating_ip_resource: Instance of openstack floating ip
    resource
    :param boolean allow_multiple: This flag to set if it is allowed to have
    networks configuration from multiple resources relationships + node
    properties
    """

    # Check to see if the floating network id is provided on the floating ip
    # config properties
    floating_ip_config = floating_ip_resource.config
    floating_network_id = floating_ip_config.get('floating_network_id')

    # Check if floating_network_name is provided
    floating_network_name = floating_ip_config.get('floating_network_name')

    # Get the floating network id from relationship if it is existed
    rel_floating_network_id = \
        _get_floating_network_id_from_relationship(NETWORK_OPENSTACK_TYPE)

    if (floating_network_id and floating_network_name or
        (floating_network_id and rel_floating_network_id) or
        (floating_network_name and rel_floating_network_id))\
            and not allow_multiple:
        raise NonRecoverableError('Floating ip can\'t have the '
                                  '"floating network properties and be '
                                  'connected to a network via a '
                                  'relationship at the same time')

    # Check if floating network name is provided or not
    if floating_network_name:
        # Create network instance to get the network id
        network = OpenstackNetwork(
            client_config=floating_ip_resource.client_config,
            logger=ctx.logger)
        # Set the network name provided in "resource_config"
        network.name = floating_network_name
        # Lookup remote network
        remote_network = network.find_network()
        if not remote_network:
            raise NonRecoverableError('Floating IP network {0} not found'
                                      ''.format(floating_network_name))
        # Set "floating_network_id" to the remote network id
        floating_network_id = remote_network.id
        # Clean "floating_network_name" from floating_ip_config since it is
        # not part of the payload request for creating floating ip
        del floating_ip_config['floating_network_name']

    # Set the final "floating_network_id" value based on the computation above
    floating_ip_config['floating_network_id'] = \
        floating_network_id or rel_floating_network_id


def _update_floating_ip_config(floating_ip_resource):
    """
    This method will try to update floating ip config with network | subnet
    | port configurations using the relationships connected with floating ip
    node
    :param dict floating_ip_resource: Instance of openstack floating ip
    resource
    """

    # Update floating ip network
    _update_floating_ip_network(floating_ip_resource)
    # Update floating ip port
    _update_floating_ip_port(floating_ip_resource)
    # Update floating ip subnet
    _update_floating_ip_subnet(floating_ip_resource)


@with_compat_node
@with_openstack_resource(class_decl=OpenstackFloatingIP,
                         existing_resource_handler=use_external_floating_ip)
def create(openstack_resource):
    """
    Create openstack floating ip instance
    :param openstack_resource: Instance of openstack floating ip resource
    """
    # Update floating ip config
    _update_floating_ip_config(openstack_resource)
    # Create openstack resource
    created_resource = openstack_resource.create()
    # Update runtime properties for floating ip
    ctx.instance.runtime_properties[RESOURCE_ID] = \
        created_resource.id
    ctx.instance.runtime_properties['floating_ip_address'] = \
        created_resource.floating_ip_address


@with_compat_node
@with_openstack_resource(OpenstackFloatingIP, ignore_unexisted_resource=True)
def delete(openstack_resource):
    """
    Delete current openstack floating ip
    :param openstack_resource: Instance of openstack floating ip resource
    """
    openstack_resource.delete()


@with_compat_node
@with_openstack_resource(OpenstackFloatingIP)
def update(openstack_resource, args):
    """
    Update openstack floating ip by passing args dict that contains the info
    that need to be updated
    :param openstack_resource: instance of openstack floating ip resource
    :param args: dict of information need to be updated
    """
    # At some case like remove ip from port, openstack API refuse to to set
    # port_id to '' empty string in order to delete the port, it should be
    # set to None in order to set it, so it is required to change '' to None
    new_config = reset_dict_empty_keys(args)
    openstack_resource.update(new_config)


@with_compat_node
@with_openstack_resource(OpenstackFloatingIP)
def list_floating_ips(openstack_resource, query=None):
    """
    List openstack floating ips based on filters applied
    :param openstack_resource: Instance of current openstack floating ip
    :param kwargs query: Optional query parameters to be sent to limit
            the floating ips being returned.
    """
    floating_ips = openstack_resource.list(query)
    add_resource_list_to_runtime_properties(
        FLOATING_IP_OPENSTACK_TYPE, floating_ips)


@with_compat_node
@with_openstack_resource(OpenstackFloatingIP)
def creation_validation(openstack_resource):
    """
    This method is to check if we can create floating ip resource in openstack
    :param openstack_resource: Instance of current openstack floating ip
    """
    validate_resource_quota(openstack_resource, FLOATING_IP_OPENSTACK_TYPE)
    ctx.logger.debug('OK: floating ip configuration is valid')
