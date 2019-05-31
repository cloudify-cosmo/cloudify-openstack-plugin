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
from openstack_sdk.resources.volume import OpenstackVolumeType
from openstack_plugin.decorators import with_openstack_resource
from openstack_plugin.constants import RESOURCE_ID


@with_openstack_resource(OpenstackVolumeType)
def create(openstack_resource):
    """
    Create openstack volume type instance
    :param openstack_resource: instance of openstack volume type resource
    """
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_openstack_resource(OpenstackVolumeType)
def delete(openstack_resource):
    """
    Delete current openstack volume type
    :param openstack_resource: instance of openstack volume type resource
    """
    if not ctx.instance.runtime_properties.get(RESOURCE_ID):
        ctx.logger.info('VolumeType is already uninitialized.')
        return
    openstack_resource.delete()
