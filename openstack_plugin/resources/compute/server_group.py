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
from openstack_sdk.resources.compute import OpenstackServerGroup
from openstack_plugin.decorators import (with_openstack_resource,
                                         with_compact_node)
from openstack_plugin.constants import (RESOURCE_ID,
                                        SERVER_GROUP_OPENSTACK_TYPE)

from openstack_plugin.utils import (validate_resource_quota,
                                    add_resource_list_to_runtime_properties)


@with_compact_node
@with_openstack_resource(OpenstackServerGroup)
def create(openstack_resource):
    """
    Create openstack server group resource
    :param openstack_resource: Instance of openstack server group resource
    """
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_compact_node
@with_openstack_resource(OpenstackServerGroup)
def delete(openstack_resource):
    """
    Delete current openstack server group
    :param openstack_resource: instance of openstack server group resource
    """
    # Delete the server group resource after lookup the resource_id values
    openstack_resource.delete()


@with_compact_node
@with_openstack_resource(OpenstackServerGroup)
def update(openstack_resource, args):
    """
    Update openstack server group by passing args dict that contains the info
    that need to be updated
    :param openstack_resource: instance of openstack server group resource
    :param args: dict of information need to be updated
    """
    # Update server group not support right now with openstack
    raise NonRecoverableError(
        'openstack library does not support update server group')


@with_compact_node
@with_openstack_resource(OpenstackServerGroup)
def list_server_groups(openstack_resource, query=None):
    """
    List openstack server groups
    :param openstack_resource: Instance of openstack sever group.
    :param kwargs query: Optional query parameters to be sent to limit
        the server groups being returned.
    """
    server_groups = openstack_resource.list(query)
    add_resource_list_to_runtime_properties(SERVER_GROUP_OPENSTACK_TYPE,
                                            server_groups)


@with_compact_node
@with_openstack_resource(OpenstackServerGroup)
def creation_validation(openstack_resource):
    """
    This method is to check if we can create server group resource in openstack
    :param openstack_resource: Instance of current openstack server group
    """
    validate_resource_quota(openstack_resource, SERVER_GROUP_OPENSTACK_TYPE)
    ctx.logger.debug('OK: server group configuration is valid')
