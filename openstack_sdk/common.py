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

# Standard imports
import uuid

# Third party imports
import openstack
import openstack.exceptions


class QuotaException(Exception):
    pass


class InvalidDomainException(Exception):
    pass


class OpenstackResource(object):
    service_type = None
    resource_type = None

    def __init__(self, client_config, resource_config=None, logger=None):
        self.client_config = client_config
        self.connection = openstack.connect(**client_config)
        self.config = resource_config or {}
        self.name = self.config.get('name')
        self.resource_id =\
            None if 'id' not in self.config else self.config['id']
        self.logger = logger
        self.validate_keystone_v3()

    def __str__(self):
        return self.name if not self.resource_id else self.resource_id

    def validate_keystone_v3(self):
        if self.auth_url and 'v3' in self.auth_url:
            client_config_keys = set(self.client_config.keys())
            for item in self.domain_auth_sets:
                common = list(item & client_config_keys)
                if len(common) == 2:
                    break
            else:
                message = 'Invalid domain combinations, they must be ' \
                          'consistent with the following patterns: {0}'
                pattern = ''
                for item in self.domain_auth_sets:
                    item = list(item)
                    pattern = pattern + '({0}, {1}),'.format(item[0], item[1])
                raise InvalidDomainException(message.format(pattern))

    def get_project_id_by_name(self, project_name=None):
        project_name = project_name or self.project_name
        project = self.connection.identity.find_project(project_name)
        if not project:
            raise openstack.exceptions.ResourceNotFound(
                'Project {0} is not found'.format(project_name))
        return project.id

    @property
    def project_name(self):
        return self.client_config.get('project_name') or  \
               self.client_config.get('tenant_name')

    @property
    def project_id(self):
        return self.config.get('project_id') or self.get_project_id_by_name()

    @property
    def auth_url(self):
        return self.client_config.get('auth_url')

    @property
    def domain_auth_sets(self):
        return [
            {'user_domain_id', 'project_domain_id'},
            {'user_domain_name', 'project_domain_name'},
            {'user_domain_id', 'project_domain_name'},
            {'user_domain_name', 'project_domain_id'},
        ]

    def validate_resource_identifier(self):
        """
        This method will validate the resource identifier whenever the
        "use_external_resource" set "True", so it will check if resource
        "id" or "name" contains a valid value before start any operation
        :return: error_message in case the resource identifier is invalid
        """
        error_message = None
        if not (self.name or self.resource_id):
            error_message = 'Resource id & name cannot be both empty'

        if self.resource_id:
            try:
                self.resource_id = str(self.resource_id)
                uuid.UUID(self.resource_id)
            except ValueError:
                # If it's a value error, then the string
                # is not a valid hex code for a UUID.
                error_message = 'Invalid resource id: {0}' \
                                ''.format(self.resource_id)

        elif self.name and not isinstance(self.name, basestring):
            error_message = 'Invalid resource name: {0} ' \
                            'this should be a string'.format(self.name)

        return error_message

    def get_quota_sets(self, quota_type):
        service_type = self.service_type
        if service_type == 'block_storage':
            service_type = 'volume'

        quota = getattr(
            self.connection,
            'get_{0}_quotas'.format(service_type))(self.project_name)

        if not quota:
            raise QuotaException(
                'Invalid {0} quota response'.format(self.service_type))

        return getattr(quota, quota_type)

    def resource_plural(self, openstack_type):
        return '{0}s'.format(openstack_type)

    def list(self):
        raise NotImplementedError()

    def get(self):
        raise NotImplementedError()

    def create(self):
        raise NotImplementedError()

    def delete(self):
        raise NotImplementedError()


class ResourceMixin(object):
    """
    This mixin used in order to filter resources that do not support filter
    based on project_id and to also to be able to find resources from
    specific projects
    """
    @staticmethod
    def get_project_id_location(item):
        return item.location.project.id

    def get_one_match(self, name_or_id, items):
        """
        This method will try to only return one resource match the
        name_or_id based on the items provided
        :param str name_or_id: The name or id of the resource
        :param items: List of instances that extend
        openstack.resource.Resource
        :return: Return target object which will be subtype of
        openstack.resource.Resource
        """
        target = None
        for resource in items:
            if (resource.id == name_or_id) or (resource.name == name_or_id):
                if target is None:
                    target = resource
                else:
                    msg = \
                        'More than one {0} ' \
                        'exists with the name {1}'.format(
                            self.resource_type, name_or_id)
                    raise openstack.exceptions.DuplicateResource(msg)
        if not target:
            raise openstack.exceptions.ResourceNotFound(
                'Resource {0} is not found'.format(name_or_id))
        return target

    def list_resources(self, query=None, all_projects=False):
        """
        This method will try to list all resources based on provided filters
        :param dict query: Dict that contains filters to use fetch resources
        :param boolean all_projects: Flag to indicate that we need to list
        all resources from all projects
        :return: List of instances that extend openstack.resource.Resource
        """
        query = query or {}
        target_resources = []

        service_type = getattr(self.connection, self.service_type)
        items = getattr(service_type, self.resource_plural(self.resource_type))
        # There is no 'project_id' filter to list some resources for specific
        # project, so in order to avoid list resources from all projects,
        # it is required to add custom filter and just return the resources we
        # care about for project
        # User also will have the ability to list resources from all projects
        # if he wants by passing "all_projects=True"
        all_projects = query.get('all_projects') or all_projects
        if not all_projects:
            project_id = query.get('project_id') or self.project_id
            if query.get('project_id'):
                del query['project_id']

            items = items(**query) if query else items()
            for item in items:
                if ResourceMixin.get_project_id_location(item) == project_id:
                    target_resources.append(item)
        else:
            target_resources = items(**query) if query else items()

        return target_resources

    def _get(self, resource_id):
        """
        This method will try to lookup openstack resource based on id if
        possible
        :param str resource_id: Resource id
        :return: Instance that extend openstack.resource.Resource
        """
        service_type = getattr(self.connection, self.service_type)
        return getattr(service_type,
                       'get_{0}'.format(self.resource_type))(resource_id)

    def find_resource(self, name_or_id):
        """
        This method will try to lookup resource if it exists
        :param str name_or_id: The name or id of the resource
        :return: Return target object which will be subtype of
        openstack.resource.Resource
        """
        if not name_or_id:
            name_or_id = self.name if not\
                self.resource_id else self.resource_id
        try:
            return self._get(name_or_id)
        except openstack.exceptions.NotFoundException:
            pass

        return self.get_one_match(name_or_id, self.list())
