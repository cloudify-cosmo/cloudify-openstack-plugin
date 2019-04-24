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

# Third part imports
import openstack.exceptions

# Local imports
from openstack_sdk.common import (OpenstackResource, ResourceMixin)


class OpenstackUser(ResourceMixin, OpenstackResource):
    service_type = 'identity'
    resource_type = 'user'
    infinite_resource_quota = 10 ** 9

    def list(self, query=None):
        return self.list_resources(query)

    def get_quota_sets(self, quota_type=None):
        return self.infinite_resource_quota

    def get(self):
        return self._find_user()

    def find_user(self, name_or_id=None):
        return self._find_user(name_or_id)

    def _find_user(self, name_or_id=None):
        if not name_or_id:
            name_or_id = self.name if not\
                self.resource_id else self.resource_id
        self.logger.debug(
            'Attempting to find this user: {0}'.format(name_or_id))
        user = self.find_resource(name_or_id)
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
        user = new_config.pop('user', None) or self.get()
        self.logger.debug(
            'Attempting to update this user: {0} with args {1}'.format(
                user, new_config))
        result = self.connection.identity.update_user(user, **new_config)
        self.logger.debug('Updated user with this result: {0}'.format(result))
        return result


class OpenstackRole(ResourceMixin, OpenstackResource):
    service_type = 'identity'
    resource_type = 'role'
    infinite_resource_quota = 10 ** 9

    def list(self, query=None):
        return self.list_resources(query)

    def get_quota_sets(self, quota_type=None):
        return self.infinite_resource_quota

    def get(self):
        return self._find_role()

    def find_role(self, name_or_id=None):
        return self._find_role(name_or_id)

    def _find_role(self, name_or_id=None):
        if not name_or_id:
            name_or_id = self.name if not\
                self.resource_id else self.resource_id
        self.logger.debug(
            'Attempting to find this role: {0}'.format(
                self.name if not self.resource_id else self.resource_id))
        role = self.find_resource(name_or_id)
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
        project = self._find_project()
        return project

    def find_project(self, name_or_id=None):
        return self._find_project(name_or_id)

    def _find_project(self, name_or_id=None):
        if not name_or_id:
            name_or_id = self.name if not \
                self.resource_id else self.resource_id
        self.logger.debug(
            'Attempting to find this project: {0}'.format(name_or_id))
        try:
            project = self.connection.identity.get_project(name_or_id)
        except openstack.exceptions.NotFoundException:
            project = self.connection.identity.find_project(
                name_or_id, ignore_missing=False
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
        project = new_config.pop('project', None) or self.get()
        self.logger.debug(
            'Attempting to update this project: {0} with args {1}'.format(
                project, new_config))
        result = self.connection.identity.update_project(project, **new_config)
        self.logger.debug(
            'Updated project with this result: {0}'.format(result))
        return result


class OpenstackDomain(OpenstackResource):
    service_type = 'identity'
    resource_type = 'domain'

    def list(self, query=None):
        query = query or {}
        return self.connection.identity.domains(**query)

    def get(self):
        return self._find_domain()

    def find_domain(self, name_or_id=None):
        return self._find_domain(name_or_id)

    def _find_domain(self, name_or_id=None):
        if not name_or_id:
            name_or_id = self.name if not \
                self.resource_id else self.resource_id
        self.logger.debug(
            'Attempting to find this domain: {0}'.format(name_or_id))
        try:
            domain = self.connection.identity.get_domain(name_or_id)
        except openstack.exceptions.NotFoundException:
            domain = self.connection.identity.find_domain(
                name_or_id, ignore_missing=False
            )
        self.logger.debug(
            'Found domain with this result: {0}'.format(domain))
        return domain

    def create(self):
        self.logger.debug(
            'Attempting to create domain with these args: {0}'.format(
                self.config))
        domain = self.connection.identity.create_domain(**self.config)
        self.logger.debug(
            'Created domain with this result: {0}'.format(domain))
        return domain

    def delete(self):
        domain = self.get()
        self.logger.debug(
            'Attempting to delete this domain: {0}'.format(domain))
        result = self.connection.identity.delete_domain(domain)
        self.logger.debug(
            'Deleted domain with this result: {0}'.format(result))
        return result

    def update(self, new_config=None):
        domain = self.get()
        self.logger.debug(
            'Attempting to update this domain: {0} with args {1}'.format(
                domain, new_config))
        result = self.connection.identity.update_domain(domain, **new_config)
        self.logger.debug(
            'Updated domain with this result: {0}'.format(result))
        return result
