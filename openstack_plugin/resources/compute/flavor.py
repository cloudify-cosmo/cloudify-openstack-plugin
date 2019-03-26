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
from openstack_sdk.resources.compute import OpenstackFlavor
from openstack_plugin.decorators import (with_openstack_resource,
                                         with_compact_node)
from openstack_plugin.constants import (RESOURCE_ID, FLAVOR_OPENSTACK_TYPE)
from openstack_plugin.utils import add_resource_list_to_runtime_properties


@with_compact_node
@with_openstack_resource(OpenstackFlavor)
def create(openstack_resource):
    """
    Create openstack flavor
    :param openstack_resource: Instance of openstack flavor resource
    """
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_compact_node
@with_openstack_resource(OpenstackFlavor)
def list_flavors(openstack_resource, query=None, details=True):
    """

    :param openstack_resource:
    :param query:
    :param details:
    :return:
    """
    flavors = openstack_resource.list(details=details, query=query)
    add_resource_list_to_runtime_properties(FLAVOR_OPENSTACK_TYPE, flavors)


@with_compact_node
@with_openstack_resource(OpenstackFlavor)
def delete(openstack_resource):
    """
    Delete flavor resource
    :param openstack_resource: Instance of openstack flavor resource.
    """
    openstack_resource.delete()


@with_compact_node
@with_openstack_resource(OpenstackFlavor)
def update(openstack_resource, args):
    """
    Update openstack flavor by passing args dict that contains the info that
    need to be updated
    :param openstack_resource: instance of openstack flavor resource
    :param args: dict of information need to be updated
    """
    # TODO This need to be uncomment whenever openstack allow for update
    #  operation since the following actions are only supported
    #  https://git.io/fh93b
    # args = reset_dict_empty_keys(args)
    # openstack_resource.update(args)
    raise NonRecoverableError(
        'Openstack SDK does not support flavor update operation')
