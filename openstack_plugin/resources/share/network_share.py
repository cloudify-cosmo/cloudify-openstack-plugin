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
from cloudify.exceptions import (OperationRetry, NonRecoverableError)
from manilaclient.common.apiclient import exceptions

# Local imports
from openstack_sdk.resources.manila import \
    OpenstackShareNetwork

from openstack_plugin.decorators import with_openstack_resource

from openstack_plugin.constants import RESOURCE_ID
from openstack_plugin.utils import (
    merge_resource_config,
    find_relationships_by_relationship_type)


@with_openstack_resource(OpenstackShareNetwork)
def create(openstack_resource, args=None):
    """
    Create openstack volume instance
    :param openstack_resource: instance of openstack volume resource
    :param args User configuration that could merge/override with
    resource configuration
    """
    args = args or {}
    networks = find_relationships_by_relationship_type(
        ctx,
        'cloudify.relationships.openstack.network_share_connected_to_network')
    if networks:
        args['neutron_net_id'] = \
            networks[0].target.instance.runtime_properties[RESOURCE_ID]
    subnets = find_relationships_by_relationship_type(
        ctx,
        'cloudify.relationships.openstack.network_share_connected_to_subnet')
    if subnets:
        args['neutron_subnet_id'] = \
            subnets[0].target.instance.runtime_properties[RESOURCE_ID]
    merge_resource_config(openstack_resource.config, args)
    try:
        created_resource = openstack_resource.create()
        ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id
        openstack_resource.update_id(created_resource.id)
    except exceptions.BadRequest as e:
        raise NonRecoverableError(e)


@with_openstack_resource(OpenstackShareNetwork)
def delete(openstack_resource):
    """
    Delete current openstack shared file system instance
    :param openstack_resource: instance of openstack shared file system
    """

    if openstack_resource.resource:
        openstack_resource.delete()
        raise OperationRetry('Network share {0} is still deleting.'.format(
            openstack_resource.resource_id))
