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

# Local imports
from openstack_sdk.resources.identity import OpenstackUser
from openstack_plugin.decorators import (with_openstack_resource,
                                         with_compact_node)
from openstack_plugin.constants import (RESOURCE_ID, USER_OPENSTACK_TYPE)
from openstack_plugin.utils import (reset_dict_empty_keys,
                                    add_resource_list_to_runtime_properties)


@with_compact_node
@with_openstack_resource(OpenstackUser)
def create(openstack_resource):
    """
    Create openstack user resource
    :param openstack_resource: Instance of openstack user resource
    """
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_compact_node
@with_openstack_resource(OpenstackUser)
def delete(openstack_resource):
    """
    Delete current openstack user
    :param openstack_resource: instance of openstack user resource
    """
    openstack_resource.delete()


@with_compact_node
@with_openstack_resource(OpenstackUser)
def update(openstack_resource, args):
    """
    Update openstack user by passing args dict that contains the info
    that need to be updated
    :param openstack_resource: instance of openstack user resource
    :param args: dict of information need to be updated
    """
    args = reset_dict_empty_keys(args)
    openstack_resource.update(args)


@with_compact_node
@with_openstack_resource(OpenstackUser)
def list_users(openstack_resource, query=None):
    """
    List openstack users
    :param openstack_resource: Instance of openstack user.
    :param kwargs query: Optional query parameters to be sent to limit
                                 the resources being returned.
    """
    users = openstack_resource.list(query)
    add_resource_list_to_runtime_properties(USER_OPENSTACK_TYPE, users)
