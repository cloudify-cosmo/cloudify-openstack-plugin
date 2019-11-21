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
    is_external_resource,
    delete_runtime_properties,
    get_openstack_id,
    set_openstack_runtime_properties,
    create_object_dict,
    add_list_to_runtime_properties,
    COMMON_RUNTIME_PROPERTIES_KEYS,
    with_resume_operation
)

RUNTIME_PROPERTIES_KEYS = COMMON_RUNTIME_PROPERTIES_KEYS
SERVER_GROUP_OPENSTACK_TYPE = 'server_group'


@operation(resumable=True)
@with_resume_operation
@with_nova_client
def create(nova_client, args, **kwargs):
    if use_external_resource(ctx, nova_client, SERVER_GROUP_OPENSTACK_TYPE):
        return

    server_grp = create_object_dict(
        ctx,
        SERVER_GROUP_OPENSTACK_TYPE,
        args,
        {'policies': [ctx.node.properties['policy']]})

    server_grp = nova_client.server_groups.create(**server_grp)
    set_openstack_runtime_properties(ctx,
                                     server_grp,
                                     SERVER_GROUP_OPENSTACK_TYPE)


@operation(resumable=True)
@with_resume_operation
@with_nova_client
def delete(nova_client, **kwargs):
    if not is_external_resource(ctx):
        ctx.logger.info('deleting server group')

        nova_client.server_groups.delete(get_openstack_id(ctx))
    else:
        ctx.logger.info('not deleting server group since an external server '
                        'group is being used')

    delete_runtime_properties(ctx, RUNTIME_PROPERTIES_KEYS)


@operation(resumable=True)
@with_resume_operation
@with_nova_client
def list_servergroups(nova_client, args, **kwargs):
    server_group_list = nova_client.server_groups.list(**args)
    add_list_to_runtime_properties(ctx,
                                   SERVER_GROUP_OPENSTACK_TYPE,
                                   server_group_list)


@operation(resumable=True)
@with_resume_operation
@with_nova_client
def creation_validation(nova_client, **kwargs):
    validate_resource(ctx, nova_client, SERVER_GROUP_OPENSTACK_TYPE)

    ctx.logger.debug('OK: server group configuration is valid')
