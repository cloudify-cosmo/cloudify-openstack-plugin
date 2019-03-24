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

# Based on this documentation:
# https://docs.openstack.org/openstacksdk/latest/user/proxies/compute.html.

# Local imports
from openstack_sdk.common import OpenstackResource


class OpenstackUser(OpenstackResource):
    service_type = 'identity'
    resource_type = 'user'

    def list(self, query=None):
        query = query or {}
        return self.connection.identity.users(**query)

    def get(self):
        self.logger.debug(
            'Attempting to find this user: {0}'.format(
                self.name if not self.resource_id else self.resource_id))
        user = self.connection.identity.get_user(
            self.name if not self.resource_id else self.resource_id
        )
        self.logger.debug('Found user with this result: {0}'.format(user))
        return user

    def find_user(self, name_or_id):
        self.logger.debug(
            'Attempting to find this user: {0}'.format(
                self.name if not self.resource_id else self.resource_id))
        user = self.connection.identity.find_user(name_or_id)
        self.logger.debug('Found user with this result: {0}'.format(user))
        return user

    def create(self):
        self.logger.debug(
            'Attempting to create user with these args: {0}'.format(
                self.config))
        user = self.connection.identity.create_user(**self.config)
        self.logger.debug('Created user with this result: {0}'.format(user))
        return user

    def delete(self):
        user = self.get()
        self.logger.debug('Attempting to delete this user: {0}'.format(user))
        result = self.connection.identity.delete_user(user)
        self.logger.debug('Deleted user with this result: {0}'.format(result))
        return result

    def update(self, new_config=None):
        user = self.get()
        self.logger.debug(
            'Attempting to update this user: {0} with args {1}'.format(
                user, new_config))
        result = self.connection.identity.update_user(user, **new_config)
        self.logger.debug('Updated user with this result: {0}'.format(result))
        return result


class OpenstackRole(OpenstackResource):
    service_type = 'identity'
    resource_type = 'role'

    def list(self, query=None):
        query = query or {}
        return self.connection.identity.roles(**query)

    def get(self):
        self.logger.debug(
            'Attempting to find this role: {0}'.format(
                self.name if not self.resource_id else self.resource_id))
        role = self.connection.identity.get_role(
            self.name if not self.resource_id else self.resource_id
        )
        self.logger.debug('Found role with this result: {0}'.format(role))
        return role

    def find_role(self, name_or_id):
        self.logger.debug(
            'Attempting to find this role: {0}'.format(
                self.name if not self.resource_id else self.resource_id))
        role = self.connection.identity.find_role(name_or_id)
        self.logger.debug('Found role with this result: {0}'.format(role))
        return role

    def assign_project_role_to_user(self, project_id, user_id, role_id):
        params = {
            'project': project_id,
            'user': user_id,
            'role': role_id
        }
        self.logger.debug(
            'Attempting to assign role to user for this project: {0}'.format(
                self.name if not self.resource_id else self.resource_id))

        self.connection.identity.assign_project_role_to_user(**params)

    def create(self):
        self.logger.debug(
            'Attempting to create role with these args: {0}'.format(
                self.config))
        role = self.connection.identity.create_role(**self.config)
        self.logger.debug('Created role with this result: {0}'.format(role))
        return role

    def delete(self):
        role = self.get()
        self.logger.debug(
            'Attempting to delete this role: {0}'.format(role))
        result = self.connection.identity.delete_role(role)
        self.logger.debug(
            'Deleted role with this result: {0}'.format(result))
        return result

    def update(self, new_config=None):
        role = self.get()
        self.logger.debug(
            'Attempting to update this role: {0} with args {1}'.format(
                role, new_config))
        result = self.connection.identity.update_role(role, **new_config)
        self.logger.debug(
            'Updated role with this result: {0}'.format(result))
        return result


class OpenstackProject(OpenstackResource):
    service_type = 'identity'
    resource_type = 'project'
    infinite_resource_quota = 10 ** 9

    def list(self, query=None):
        query = query or {}
        return self.connection.identity.projects(**query)

    def get_quota_sets(self, quota_type=None):
        return self.infinite_resource_quota

    def get(self):
        self.logger.debug(
            'Attempting to find this project: {0}'.format(
                self.name if not self.resource_id else self.resource_id))
        project = self.connection.identity.get_project(
            self.name if not self.resource_id else self.resource_id
        )
        self.logger.debug(
            'Found project with this result: {0}'.format(project))
        return project

    def create(self):
        self.logger.debug(
            'Attempting to create project with these args: {0}'.format(
                self.config))
        project = self.connection.identity.create_project(**self.config)
        self.logger.debug(
            'Created project with this result: {0}'.format(project))
        return project

    def delete(self):
        project = self.get()
        self.logger.debug(
            'Attempting to delete this project: {0}'.format(project))
        result = self.connection.identity.delete_project(project)
        self.logger.debug(
            'Deleted project with this result: {0}'.format(result))
        return result

    def update(self, new_config=None):
        project = self.get()
        self.logger.debug(
            'Attempting to update this project: {0} with args {1}'.format(
                project, new_config))
        result = self.connection.identity.update_project(project, **new_config)
        self.logger.debug(
            'Updated project with this result: {0}'.format(result))
        return result
