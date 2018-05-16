#########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
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
from cloudify.exceptions import NonRecoverableError

from openstack_plugin_common import (with_keystone_client,
                                     with_nova_client,
                                     with_cinder_client,
                                     with_neutron_client,
                                     get_openstack_id,
                                     use_external_resource,
                                     delete_resource_and_runtime_properties,
                                     add_list_to_runtime_properties,
                                     validate_resource,
                                     create_object_dict,
                                     set_openstack_runtime_properties,
                                     COMMON_RUNTIME_PROPERTIES_KEYS)


PROJECT_OPENSTACK_TYPE = 'project'

PROJECT_QUOTA_TYPE = 'quota'

RUNTIME_PROPERTIES_KEYS = COMMON_RUNTIME_PROPERTIES_KEYS

NOVA = 'nova'
CINDER = 'cinder'
NEUTRON = 'neutron'

QUOTA = 'quota'
USERS = 'users'
ROLES = 'roles'


@operation
@with_keystone_client
def create(keystone_client, args, **kwargs):
    if use_external_resource(ctx, keystone_client, PROJECT_OPENSTACK_TYPE):
        return

    project_dict = create_object_dict(ctx,
                                      PROJECT_OPENSTACK_TYPE,
                                      args,
                                      {'domain': 'default'})

    project = keystone_client.projects.create(**project_dict)
    set_openstack_runtime_properties(ctx, project, PROJECT_OPENSTACK_TYPE)


@operation
def start(quota_dict, **kwargs):
    users = ctx.node.properties[USERS]
    validate_users(users, **kwargs)
    assign_users(users, **kwargs)
    quota = ctx.node.properties[PROJECT_QUOTA_TYPE]
    quota.update(quota_dict)
    update_project_quota(quota=quota, **kwargs)


@operation
@with_keystone_client
@with_nova_client
@with_cinder_client
@with_neutron_client
def delete(keystone_client, nova_client, cinder_client,
           neutron_client, **kwargs):
    project_id = get_openstack_id(ctx)
    quota = ctx.node.properties[PROJECT_QUOTA_TYPE]
    delete_quota(project_id, quota, nova_client, NOVA)
    delete_quota(project_id, quota, neutron_client, NEUTRON)
    delete_quota(project_id, quota, cinder_client, CINDER)
    delete_resource_and_runtime_properties(ctx, keystone_client,
                                           RUNTIME_PROPERTIES_KEYS)


@operation
@with_keystone_client
def creation_validation(keystone_client, **kwargs):
    validate_resource(ctx, keystone_client, PROJECT_OPENSTACK_TYPE)


@with_keystone_client
def assign_users(users, keystone_client, **kwargs):
    project_id = get_openstack_id(ctx)
    for user in users:
        roles = user[ROLES]
        u = keystone_client.users.find(name=user['name'])
        for role in roles:
            r = keystone_client.roles.find(name=role)
            keystone_client.roles.grant(user=u.id,
                                        project=project_id,
                                        role=r.id)
            ctx.logger.debug("Assigned user {0} to project {1} with role {2}"
                             .format(u.id, project_id, r.id))


@with_keystone_client
def validate_users(users, keystone_client, **kwargs):
    user_names = [user['name'] for user in users]
    if len(user_names) > len(set(user_names)):
        raise NonRecoverableError('Users are not unique')

    for user_name in user_names:
        keystone_client.users.find(name=user_name)

    for user in users:
        if len(user[ROLES]) > len(set(user[ROLES])):
            msg = 'Roles for user {} are not unique'
            raise NonRecoverableError(msg.format(user['name']))

    role_names = {role for user in users for role in user[ROLES]}
    for role_name in role_names:
        keystone_client.roles.find(name=role_name)


def get_quota(tenant_id, client, what_quota):
    if what_quota == NEUTRON:
        quota = dict(client.show_quota(tenant_id=tenant_id)).get('quota')
    else:
        quota = client.quotas.get(tenant_id=tenant_id).to_dict()

    ctx.logger.debug(
        'Got {0} quota: {1}'.format(what_quota, str(quota)))

    return quota


def update_quota(tenant_id, quota, client, what_quota):
    updated_quota = quota.get(what_quota)
    if updated_quota:
        if what_quota == NEUTRON:
            new_quota = client.update_quota(tenant_id=tenant_id,
                                            body={QUOTA: updated_quota})
        else:
            new_quota = client.quotas.update(tenant_id=tenant_id,
                                             **updated_quota)
        ctx.logger.debug(
            'Updated {0} quota: {1}'.format(what_quota, str(new_quota)))


def delete_quota(project_id, quota, client, what_quota):
    deleting_quota = quota.get(what_quota)
    if deleting_quota:
        if what_quota == NEUTRON:
            client.delete_quota(tenant_id=project_id)
        else:
            client.quotas.delete(tenant_id=project_id)
        ctx.logger.debug(
            'Deleted {0} quota'.format(what_quota))


@with_nova_client
@with_neutron_client
@with_cinder_client
def update_project_quota(nova_client,
                         cinder_client,
                         neutron_client,
                         quota,
                         **kwargs):
    project_id = get_openstack_id(ctx)
    update_quota(project_id, quota, nova_client, NOVA)
    update_quota(project_id, quota, neutron_client, NEUTRON)
    update_quota(project_id, quota, cinder_client, CINDER)


@with_keystone_client
def list_projects(keystone_client, args, **kwargs):
    projects_list = keystone_client.projects.list(**args)
    add_list_to_runtime_properties(ctx, PROJECT_OPENSTACK_TYPE, projects_list)


@with_nova_client
@with_neutron_client
@with_cinder_client
def get_project_quota(nova_client,
                      cinder_client,
                      neutron_client,
                      **kwargs):
    project_id = get_openstack_id(ctx)
    quota = ctx.instance.runtime_properties.get(QUOTA, {})
    quota[NOVA] = get_quota(project_id, nova_client, NOVA)
    quota[NEUTRON] = get_quota(project_id, neutron_client, NEUTRON)
    quota[CINDER] = get_quota(project_id, cinder_client, CINDER)
    ctx.instance.runtime_properties[QUOTA] = quota


@with_keystone_client
def update_project(keystone_client, args, **kwargs):

    project_dict = create_object_dict(ctx,
                                      PROJECT_OPENSTACK_TYPE,
                                      args,
                                      {'domain': 'default'})
    project_dict[PROJECT_OPENSTACK_TYPE] = get_openstack_id(ctx)
    project = keystone_client.projects.update(**project_dict)
    set_openstack_runtime_properties(ctx, project, PROJECT_OPENSTACK_TYPE)
