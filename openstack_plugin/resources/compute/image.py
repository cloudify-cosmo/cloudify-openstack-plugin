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
from openstack_sdk.resources.images import OpenstackImage
from openstack_plugin.decorators import (with_openstack_resource,
                                         with_compat_node)
from openstack_plugin.constants import (RESOURCE_ID, IMAGE_OPENSTACK_TYPE)
from openstack_plugin.utils import (validate_resource_quota,
                                    reset_dict_empty_keys,
                                    add_resource_list_to_runtime_properties)


@with_compat_node
@with_openstack_resource(OpenstackImage)
def create(openstack_resource):
    # TODO Need to handle image upload to openstack when image_url is
    #  specified even if it is local url or remote url
    # image_url = ctx.node.properties.get('image_url')
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_compat_node
@with_openstack_resource(OpenstackImage)
def start(openstack_resource):
    # TODO This should be implemented in order to check if uploading image
    #  is done or not
    pass


@with_compat_node
@with_openstack_resource(OpenstackImage)
def delete(openstack_resource):
    # Delete the image resource after lookup the resource_id values
    openstack_resource.delete()


@with_compat_node
@with_openstack_resource(OpenstackImage)
def update(openstack_resource, args):
    """
    Update openstack image by passing args dict that contains the info that
    need to be updated
    :param openstack_resource: instance of openstack image resource
    :param args: dict of information need to be updated
    """
    args = reset_dict_empty_keys(args)
    openstack_resource.update(args)


@with_compat_node
@with_openstack_resource(OpenstackImage)
def list_images(openstack_resource, query=None):
    """
    List openstack images based on filters applied
    :param openstack_resource: Instance of current openstack image
    :param kwargs query: Optional query parameters to be sent to limit
                                 the resources being returned.
    """
    images = openstack_resource.list(query)
    add_resource_list_to_runtime_properties(IMAGE_OPENSTACK_TYPE, images)


@with_compat_node
@with_openstack_resource(OpenstackImage)
def creation_validation(openstack_resource):
    """
    This method is to check if we can create image resource in openstack
    :param openstack_resource: Instance of current openstack image
    """
    validate_resource_quota(openstack_resource, IMAGE_OPENSTACK_TYPE)
    ctx.logger.debug('OK: image configuration is valid')
