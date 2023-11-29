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
    OpenstackFileShare

from openstack_plugin.decorators import with_openstack_resource

from openstack_plugin.constants import RESOURCE_ID
from openstack_plugin.utils import (
    merge_resource_config,
    find_relationships_by_relationship_type)


@with_openstack_resource(OpenstackFileShare)
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
        'cloudify.relationships.openstack.share_connected_to_network_share')
    if networks:
        args['share_network'] = \
            networks[0].target.instance.runtime_properties[RESOURCE_ID]
    merge_resource_config(openstack_resource.config, args)
    resource = openstack_resource.get()
    if not resource:
        try:
            resource = openstack_resource.create()
            ctx.instance.runtime_properties[RESOURCE_ID] = resource.id
            openstack_resource.update_id(resource.id)
        except exceptions.BadRequest as e:
            raise NonRecoverableError(e)

    if openstack_resource.error:
        raise NonRecoverableError('Failed to create share, status: error.')
    elif not openstack_resource.ready:
        raise OperationRetry(
            'Create status is {0}. Waiting for available status.'.format(
                resource.status))


@with_openstack_resource(OpenstackFileShare)
def delete(openstack_resource):
    """
    Delete current openstack shared file system instance
    :param openstack_resource: instance of openstack shared file system
    """

    if openstack_resource.ready:
        openstack_resource.delete()

    if openstack_resource.delete_failed:
        raise NonRecoverableError('Failed to delete the resource {0}.'.format(
            openstack_resource.resource_id))
    elif not openstack_resource.resource:
        ctx.logger.info('Shared resource {0} is deleted successfully'.format(
            openstack_resource.resource_id))
    else:
        raise OperationRetry(
            'Shared resource {0} is still being deleted. Status: {1}'.format(
                openstack_resource.resource_id,
                openstack_resource.resource.status))


@with_openstack_resource(OpenstackFileShare)
def allow(openstack_resource, **kwargs):
    kwargs = kwargs or {}
    if 'access' not in kwargs:
        ctx.logger.error(
            'In order to grant access to a share, '
            'the IP must be provided as "access".')
    share = openstack_resource.allow(**kwargs)
    ctx.target.instance.runtime_properties['export'] = share.export_locations


@with_openstack_resource(OpenstackFileShare)
def deny(openstack_resource, **kwargs):
    kwargs = kwargs or {}
    if 'access' not in kwargs:
        ctx.logger.error(
            'In order to deny access to a share, '
            'the IP must be provided as "access".')
    openstack_resource.deny(kwargs['access'])
