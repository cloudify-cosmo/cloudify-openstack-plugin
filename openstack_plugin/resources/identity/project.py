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
from openstack_sdk.resources.identity import (OpenstackProject,
                                              OpenstackUser,
                                              OpenstackGroup,
                                              OpenstackRole)
from openstack_plugin.decorators import (with_openstack_resource,
                                         with_compat_node)

from openstack_plugin.constants import (RESOURCE_ID,
                                        PROJECT_OPENSTACK_TYPE,
                                        IDENTITY_USERS,
                                        IDENTITY_GROUPS,
                                        IDENTITY_ROLES,
                                        IDENTITY_QUOTA)

from openstack_plugin.utils import (validate_resource_quota,
                                    reset_dict_empty_keys,
                                    add_resource_list_to_runtime_properties)


def _assign_groups(project_resource, groups):
    """
    Assign groups to project
    :param project_resource: project resource instance (OpenstackProject)
    :param groups: List of groups that need to be assigned to project with
    roles
    """
    # Create group resource to be able to get info about group
    group_resource = OpenstackGroup(
        client_config=project_resource.client_config,
        logger=ctx.logger
    )

    # Create group role resource to be able to get info about role
    role_resource = OpenstackRole(
        client_config=project_resource.client_config,
        logger=ctx.logger
    )

    for group in groups:
        group_roles = group.get(IDENTITY_ROLES, [])
        group_item = group_resource.find_group(group.get('name'))
        if not group_item:
            raise NonRecoverableError('Group {0} is not found'
                                      ''.format(group['name']))

        for role in group_roles:
            group_role = role_resource.find_role(role)
            if not group_role:
                raise NonRecoverableError('Role {0} is not found'.format(role))

            # Assign project role to group
            role_resource.assign_project_role_to_group(
                project_id=project_resource.resource_id,
                group_id=group_item.id,
                role_id=group_role.id)

            ctx.logger.info(
                'Assigned group {0} to project {1} with role {2}'.format(
                    group_item.id, project_resource.resource_id,
                    group_role.id))


def _validate_groups(client_config, groups):
    """
    This method will validate if the groups are already exists before doing
    any role assignment. Morever, it will check if the roles also exist or not
    :param list groups: List of groups (dict) that contains group names and
    roles associated
    :param client_config: Openstack configuration in order to connect to
    openstack
    """

    # Create group resource to be able to get info about group
    group_resource = OpenstackGroup(client_config=client_config,
                                    logger=ctx.logger)

    # Create group role resource to be able to get info about role
    role_resource = OpenstackRole(client_config=client_config,
                                  logger=ctx.logger)

    group_names = [group.get('name') for group in groups]
    if len(group_names) > len(set(group_names)):
        raise NonRecoverableError(' Provided groups are not unique')

    for group_name in group_names:
        group = group_resource.find_group(group_name)
        if not group:
            raise NonRecoverableError(
                'Group {0} is not found'.format(group_name))

    for group in groups:
        if group.get(IDENTITY_ROLES):
            if len(group[IDENTITY_ROLES]) > len(set(group[IDENTITY_ROLES])):
                msg = 'Roles for group {0} are not unique'
                raise NonRecoverableError(msg.format(group.get('name')))

    role_names = {
        role for group in groups for role in group.get(IDENTITY_ROLES, [])
    }
    for role_name in role_names:
        group_role = role_resource.find_role(role_name)
        if not group_role:
            raise NonRecoverableError(
                'Role {0} is not found'.format(role_name))


def _assign_users(project_resource, users):
    """
    Assign users to project
    :param project_resource: project resource instance (OpenstackProject)
    :param users: List of users that need to be assigned to project with roles
    """
    # Create user resource to be able to get info about user
    user_resource = OpenstackUser(
        client_config=project_resource.client_config,
        logger=ctx.logger
    )

    # Create user role resource to be able to get info about role
    role_resource = OpenstackRole(
        client_config=project_resource.client_config,
        logger=ctx.logger
    )

    for user in users:
        user_roles = user.get(IDENTITY_ROLES, [])
        user_item = user_resource.find_user(user.get('name'))
        if not user_item:
            raise NonRecoverableError('User {0} is not found'
                                      ''.format(user['name']))

        for role in user_roles:
            user_role = role_resource.find_role(role)
            if not user_role:
                raise NonRecoverableError('Role {0} is not found'.format(role))

            # Assign project role to user
            role_resource.assign_project_role_to_user(
                project_id=project_resource.resource_id,
                user_id=user_item.id,
                role_id=user_role.id)

            ctx.logger.info(
                'Assigned user {0} to project {1} with role {2}'.format(
                    user_item.id, project_resource.resource_id, user_role.id))


def _validate_users(client_config, users):
    """
    This method will validate if the users are already exists before doing
    any role assignment. Morever, it will check if the roles also exist or not
    :param list users: List of users (dict) that contains user names and
    roles associated
    :param client_config: Openstack configuration in order to connect to
    openstack
    """

    # Create user resource to be able to get info about user
    user_resource = OpenstackUser(client_config=client_config,
                                  logger=ctx.logger)

    # Create user role resource to be able to get info about role
    role_resource = OpenstackRole(client_config=client_config,
                                  logger=ctx.logger)

    user_names = [user.get('name') for user in users]
    if len(user_names) > len(set(user_names)):
        raise NonRecoverableError(' Provided users are not unique')

    for user_name in user_names:
        user = user_resource.find_user(user_name)
        if not user:
            raise NonRecoverableError(
                'User {0} is not found'.format(user_name))

    for user in users:
        if user.get(IDENTITY_ROLES):
            if len(user[IDENTITY_ROLES]) > len(set(user[IDENTITY_ROLES])):
                msg = 'Roles for user {0} are not unique'
                raise NonRecoverableError(msg.format(user.get('name')))

    role_names = {
        role for user in users for role in user.get(IDENTITY_ROLES, [])
    }
    for role_name in role_names:
        user_role = role_resource.find_role(role_name)
        if not user_role:
            raise NonRecoverableError(
                'Role {0} is not found'.format(role_name))


def _handle_external_project_resource(openstack_resource):
    """
    This method will check for the users list if provided and it will
    assign that list with their roles to this external/existing project
    """
    existing_project = openstack_resource.get()
    if not existing_project:
        ctx.logger.info("this project is not valid / does not exist")
        return
    users = ctx.node.properties.get(IDENTITY_USERS, [])
    if users:
        _validate_users(openstack_resource.client_config, users)
        _assign_users(openstack_resource, users)
    else:
        ctx.logger.info("no users to add to this project")

    groups = ctx.node.properties.get(IDENTITY_GROUPS)
    if groups:
        _validate_groups(openstack_resource.client_config, groups)
        _assign_groups(openstack_resource, groups)
    else:
        ctx.logger.info("no groups to add to this project")


@with_compat_node
@with_openstack_resource(
    OpenstackProject,
    existing_resource_handler=_handle_external_project_resource)
def create(openstack_resource):
    """
    Create openstack project resource
    :param openstack_resource: Instance of openstack project resource
    """
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_compat_node
@with_openstack_resource(OpenstackProject)
def start(openstack_resource, quota_dict={}):
    """
    Prepare users to be added to created project
    :param openstack_resource: Instance of openstack project resource
    :param quota_dict: Configuration to update project quota
    """

    # Check if project node has associated users that should be added
    if ctx.node.properties.get(IDENTITY_USERS):

        # Before start assigning roles user, there is a validation that must be
        # run first to check if the the provided users and their roles are
        # already exist
        users = ctx.node.properties[IDENTITY_USERS]
        _validate_users(openstack_resource.client_config, users)

        # Assign project role to users
        _assign_users(openstack_resource, users)

    # Check if project node has associated groups that should be added
    if ctx.node.properties.get(IDENTITY_GROUPS):

        # Before start assigning roles group, there is a validation that must
        # be run first to check if the the provided groups and their roles are
        # already exist
        groups = ctx.node.properties[IDENTITY_GROUPS]
        _validate_groups(openstack_resource.client_config, groups)

        # Assign project role to groups
        _assign_groups(openstack_resource, groups)

    # Check if project node has quota information that should be updated for
    # project
    # TODO The openstack should be extended in order to add support for
    #  quota update
    if ctx.node.properties.get(IDENTITY_QUOTA) or quota_dict:
        raise NonRecoverableError('Openstack SDK does not support updating '
                                  'quota for project')


@with_compat_node
@with_openstack_resource(OpenstackProject)
def delete(openstack_resource):
    """
    Delete current openstack project
    :param openstack_resource: instance of openstack project resource
    """
    openstack_resource.delete()


@with_compat_node
@with_openstack_resource(OpenstackProject)
def update(openstack_resource, args):
    """
    Update openstack project by passing args dict that contains the info
    that need to be updated
    :param openstack_resource: instance of openstack project resource
    :param args: dict of information need to be updated
    """
    args = reset_dict_empty_keys(args)
    openstack_resource.update(args)


@with_compat_node
@with_openstack_resource(OpenstackProject)
def list_projects(openstack_resource, query=None):
    """
    List openstack projects
    :param openstack_resource: Instance of openstack project.
    :param kwargs query: Optional query parameters to be sent to limit
                                 the resources being returned.
    """
    projects = openstack_resource.list(query)
    add_resource_list_to_runtime_properties(PROJECT_OPENSTACK_TYPE, projects)


@with_compat_node
@with_openstack_resource(OpenstackProject)
def creation_validation(openstack_resource):
    """
    This method is to check if we can create project resource in openstack
    :param openstack_resource: Instance of current openstack project
    """
    validate_resource_quota(openstack_resource, PROJECT_OPENSTACK_TYPE)
    ctx.logger.debug('OK: project configuration is valid')


@with_compat_node
@with_openstack_resource(OpenstackProject)
def get_project_quota(openstack_resource):
    """
    This method is to get quota for project resource in openstack
    :param openstack_resource: Instance of current openstack project
    """
    # TODO The openstack should be extended in order to add support for
    #  retrieving quota for project
    raise NonRecoverableError('Openstack SDK does not support retrieving '
                              'quota for project')


@with_compat_node
@with_openstack_resource(OpenstackProject)
def update_project_quota(openstack_resource, quota={}):
    """
    This method is to update quota project resource in openstack
    :param openstack_resource: Instance of current openstack project
    :param quota: Quota configuration
    """
    # TODO The openstack should be extended in order to add support for
    #  get update
    raise NonRecoverableError('Openstack SDK does not support updating '
                              'quota for project')
