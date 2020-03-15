# #######
# Copyright (c) 2020 Cloudify Platform Ltd. All rights reserved
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
from openstack_sdk.resources.dns_service import OpenstackZone
from openstack_plugin.decorators import (with_openstack_resource,
                                         with_compat_node)
from openstack_plugin.constants import (RESOURCE_ID)


@with_compat_node
@with_openstack_resource(OpenstackZone)
def create(openstack_resource):
    """
    Create openstack DNS Zone
    :param openstack_resource: Instance of openstack Zone resource
    """
    created_resource = openstack_resource.create()
    # remove status from returned object , it will be pending
    created_resource.pop("status", None)
    ctx.instance.runtime_properties['Properties'] = created_resource
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_compat_node
@with_openstack_resource(OpenstackZone)
def delete(openstack_resource):
    """
    Delete DNS Zone resource
    :param openstack_resource: Instance of openstack Zone resource.
    """
    openstack_resource.delete()
    ctx.instance.runtime_properties.pop('Properties', None)
    ctx.instance.runtime_properties.pop(RESOURCE_ID, None)
