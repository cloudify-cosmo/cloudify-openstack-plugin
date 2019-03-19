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


class QuotaException(Exception):
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

    def __str__(self):
        return self.name if not self.resource_id else self.resource_id

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
        project_name = self.client_config.get('project_name')
        quota = getattr(
            self.connection,
            'get_{0}_quotas'.format(self.service_type))(project_name)

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
