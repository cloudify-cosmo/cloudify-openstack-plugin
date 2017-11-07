#########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.

from cloudify import ctx
from cloudify.decorators import operation
from openstack_plugin_common import (
    with_nova_client,
    validate_resource,
    use_external_resource,
    transform_resource_name,
    is_external_resource,
    delete_runtime_properties,
    get_resource_id,
    OPENSTACK_ID_PROPERTY,
    OPENSTACK_TYPE_PROPERTY,
    OPENSTACK_NAME_PROPERTY,
    COMMON_RUNTIME_PROPERTIES_KEYS
)

RUNTIME_PROPERTIES_KEYS = COMMON_RUNTIME_PROPERTIES_KEYS
SERVER_GROUP_OPENSTACK_TYPE = 'server_group'


@operation
@with_nova_client
def create(nova_client, args, **kwargs):

    if use_external_resource(ctx, nova_client, SERVER_GROUP_OPENSTACK_TYPE):
        return

    server_grp = {
        'name': get_resource_id(ctx, SERVER_GROUP_OPENSTACK_TYPE),
        'policies': [ctx.node.properties['policy']]
    }
    transform_resource_name(ctx, server_grp)

    server_grp = nova_client.server_groups.create(**server_grp)
    ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY] = server_grp.id
    ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY] = \
        SERVER_GROUP_OPENSTACK_TYPE
    ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY] = server_grp.name


@operation
@with_nova_client
def delete(nova_client, **kwargs):
    if not is_external_resource(ctx):
        ctx.logger.info('deleting server group')

        nova_client.server_groups.delete(
            ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY])
    else:
        ctx.logger.info('not deleting server group since an external server '
                        'group is being used')

    delete_runtime_properties(ctx, RUNTIME_PROPERTIES_KEYS)


@operation
@with_nova_client
def creation_validation(nova_client, **kwargs):

    validate_resource(ctx, nova_client, SERVER_GROUP_OPENSTACK_TYPE)

    ctx.logger.debug('OK: server group configuration is valid')
