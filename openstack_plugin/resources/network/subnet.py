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
from openstack_sdk.resources.networks import OpenstackSubnet
from openstack_plugin.decorators import (with_openstack_resource,
                                         with_compat_node,
                                         with_multiple_data_sources)

from openstack_plugin.constants import (RESOURCE_ID,
                                        SUBNET_OPENSTACK_TYPE,
                                        NETWORK_OPENSTACK_TYPE)
from openstack_plugin.utils import (
    reset_dict_empty_keys,
    validate_resource_quota,
    add_resource_list_to_runtime_properties,
    find_openstack_ids_of_connected_nodes_by_openstack_type,
    validate_ip_or_range_syntax)


def _get_subnet_network_id_from_relationship():
    """
    This method will lookup the network id for subnet using relationship
    and will raise error if it returns multiple network
    :return str network_id: Network id
    """
    # Get the network id from relationship if it is existed
    network_ids = find_openstack_ids_of_connected_nodes_by_openstack_type(
        ctx, NETWORK_OPENSTACK_TYPE)
    # Check if subnet is connected to multiple networks
    if len(network_ids) > 1:
        raise NonRecoverableError('Cannot attach subnet to multiple '
                                  'networks {0}'.format(','.join(network_ids)))

    return network_ids[0] if network_ids else None


@with_multiple_data_sources()
def _update_subnet_config(subnet_config, allow_multiple=False):
    """
    This method will try to update subnet config with network configurations
    using the relationships connected with subnet node
    :param dict subnet_config: The subnet configuration required in order to
    create the subnet instance using Openstack API
    :param boolean allow_multiple: This flag to set if it is allowed to have
    networks configuration from multiple resources relationships + node
    properties
    """

    # Check to see if the network id is provided on the subnet config
    # properties
    network_id = subnet_config.get('network_id')

    # Get the network id from relationship if it is existed
    rel_network_id = _get_subnet_network_id_from_relationship()
    if network_id and rel_network_id and not allow_multiple:
        raise NonRecoverableError('Subnet can\'t both have the '
                                  '"network_id" property and be '
                                  'connected to a network via a '
                                  'relationship at the same time')

    subnet_config['network_id'] = network_id or rel_network_id


def _handle_external_subnet_resource(openstack_resource):
    """
    This method is to do a validation for external subnet resource when it
    is connected to network node resource
    :param openstack_resource: Instance of openstack subnet resource
    """
    network_id = _get_subnet_network_id_from_relationship()
    remote_subnet = openstack_resource.get()
    if network_id and network_id != remote_subnet.network_id:
        raise NonRecoverableError(
            'Expected external resources subnet {0} and network'
            ' {1} to be connected'.format(remote_subnet.id, network_id))


@with_compat_node
@with_openstack_resource(
    OpenstackSubnet,
    existing_resource_handler=_handle_external_subnet_resource)
def create(openstack_resource):
    """
    Create openstack subnet instance
    :param openstack_resource: instance of openstack subnet resource
    """
    # Update subnet config before send create API request
    _update_subnet_config(openstack_resource.config)
    # Create subnet resource
    created_resource = openstack_resource.create()
    # Save resource id as runtime property
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_compat_node
@with_openstack_resource(OpenstackSubnet)
def delete(openstack_resource):
    """
    Delete current openstack subnet
    :param openstack_resource: instance of openstack subnet resource
    """
    openstack_resource.delete()


@with_compat_node
@with_openstack_resource(OpenstackSubnet)
def update(openstack_resource, args):
    """
    Update openstack subnet by passing args dict that contains the info that
    need to be updated
    :param openstack_resource: instance of openstack subnet resource
    :param args: dict of information need to be updated
    """
    args = reset_dict_empty_keys(args)
    openstack_resource.update(args)


@with_compat_node
@with_openstack_resource(OpenstackSubnet)
def list_subnets(openstack_resource, query=None):
    """
    List openstack subnets based on filters applied
    :param openstack_resource: Instance of current openstack network
    :param kwargs query: Optional query parameters to be sent to limit
            the networks being returned.
    """
    subnets = openstack_resource.list(query)
    add_resource_list_to_runtime_properties(SUBNET_OPENSTACK_TYPE, subnets)


@with_compat_node
@with_openstack_resource(OpenstackSubnet)
def creation_validation(openstack_resource, args={}):
    """
    This method is to check if we can create subnet resource in openstack
    :param openstack_resource: Instance of current openstack subnet
    :param dict args: Subnet Configuration
    """
    validate_resource_quota(openstack_resource, SUBNET_OPENSTACK_TYPE)
    ctx.logger.debug('OK: subnet configuration is valid')

    subnet = dict(openstack_resource.config, **args)

    if 'cidr' not in subnet:
        err = '"cidr" property must appear under the "subnet" property of a ' \
              'subnet node'
        ctx.logger.error('VALIDATION ERROR: ' + err)
        raise NonRecoverableError(err)
    validate_ip_or_range_syntax(ctx, subnet['cidr'])
