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
from openstack_sdk.resources.compute import OpenstackKeyPair
from openstack_plugin.decorators import (with_openstack_resource,
                                         with_compat_node)
from openstack_plugin.constants import (RESOURCE_ID, KEYPAIR_OPENSTACK_TYPE)
from openstack_plugin.utils import (validate_resource_quota,
                                    add_resource_list_to_runtime_properties)


@with_compat_node
@with_openstack_resource(OpenstackKeyPair)
def create(openstack_resource):
    """
    Create openstack keypair resource
    :param openstack_resource: Instance of openstack keypair resource
    """
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = \
        created_resource.id
    ctx.instance.runtime_properties['private_key'] = \
        created_resource.private_key
    ctx.instance.runtime_properties['public_key'] = \
        created_resource.public_key


@with_compat_node
@with_openstack_resource(OpenstackKeyPair)
def delete(openstack_resource):
    """
    Delete current openstack keypair
    :param openstack_resource: instance of openstack keypair resource
    """
    if not ctx.instance.runtime_properties.get(RESOURCE_ID):
        ctx.logger.info('KeyPair is already uninitialized.')
        return
    openstack_resource.delete()


@with_compat_node
@with_openstack_resource(OpenstackKeyPair)
def list_keypairs(openstack_resource):
    """
    List openstack keypairs
    :param openstack_resource: Instance of openstack keypair.
    """
    keypairs = openstack_resource.list()
    add_resource_list_to_runtime_properties(KEYPAIR_OPENSTACK_TYPE, keypairs)


@with_compat_node
@with_openstack_resource(OpenstackKeyPair)
def creation_validation(openstack_resource):
    """
    This method is to check if we can create keypair resource in openstack
    :param openstack_resource: Instance of current openstack keypair
    """
    validate_resource_quota(openstack_resource, KEYPAIR_OPENSTACK_TYPE)
    ctx.logger.debug('OK: key pair configuration is valid')
