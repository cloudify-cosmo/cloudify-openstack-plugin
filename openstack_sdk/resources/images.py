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
from openstack_sdk.common import (OpenstackResource, ResourceMixin)


class OpenstackImage(ResourceMixin, OpenstackResource):
    service_type = 'image'
    resource_type = 'image'
    infinite_resource_quota = 10 ** 9

    def list(self, query=None, all_projects=False):
        return self.list_resources(query, all_projects)

    def get_quota_sets(self, quota_type=None):
        return self.infinite_resource_quota

    def get(self):
        self.logger.debug(
            'Attempting to find this image: {0}'.format(self.resource_id))
        image = self.connection.image.get_image(self.resource_id)
        self.logger.debug('Found image with this result: {0}'.format(image))
        return image

    def find_image(self, name_or_id=None):
        self.logger.debug('Attempting to find this image: {0}'
                          ''.format(name_or_id))
        image = self.find_resource(name_or_id)
        self.logger.debug('Found image with this result: {0}'.format(image))
        return image

    def create(self):
        self.logger.debug(
            'Attempting to create image with these args: {0}'.format(
                self.config))
        image = self.connection.image.upload_image(**self.config)
        self.logger.debug(
            'Created image with this result: {0}'.format(image))
        return image

    def delete(self):
        image = self.get()
        self.logger.debug(
            'Attempting to delete this image: {0}'.format(image))
        self.connection.image.delete_image(image)

    def update(self, new_config=None):
        image = self.get()
        self.logger.debug(
            'Attempting to update this image: {0} with args {1}'.format(
                image, new_config))
        result = self.connection.image.update_image(image, **new_config)
        self.logger.debug(
            'Updated image with this result: {0}'.format(result))
        return result
