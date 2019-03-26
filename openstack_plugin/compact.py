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


# Local imports
from openstack_plugin.constants import USE_EXTERNAL_RESOURCE_PROPERTY


FLAVOR_RESOURCE_CONFIG = (
    'description',
    'ram',
    'disk',
    'vcpus'
)


class Compact(object):
    def __init__(self, context):
        """
        This will set current node context in order to help do the
        transformation process
        :param context: Cloudify context cloudify.context.CloudifyContext
        """
        self.context = context
        self._properties = self.context.node.properties
        self._type = self.context.node.type

    def get_transformation_handler(self):
        return {
            'cloudify.openstack.nodes.Flavor': self._transform_flavor
        }

    def get_common_properties(self):
        """
        This method will prepare common compatible openstack version 3
        properties
        :return dict: Common Compatible openstack version 3 properties
        """
        common = dict()
        # Populate client config from openstack config
        if self._properties.get('openstack_config'):
            common['client_config'] = self._properties['openstack_config']

        common['resource_config'] = dict()
        common['resource_config']['kwargs'] = dict()
        # Check if use external resource is set to "True" so that we can
        # update the resource config with external resource id
        if self._properties.get(USE_EXTERNAL_RESOURCE_PROPERTY):
            common['resource_config']['id'] = \
                self._properties.get('resource_iud')
        else:
            common['resource_config']['name'] = \
                self._properties.get('resource_id')

        return common

    def _transform_flavor(self):
        """
        This method will do transform operation for flavor node to be
        compatible with openstack flavor version 3
        :return dict: Compatible flavor openstack version 3 properties
        """
        common = self.get_common_properties()
        for key, value in self._properties.get('flavor', {}).items():
            if key in FLAVOR_RESOURCE_CONFIG:
                common['resource_config'][key] = value
            else:
                common['resource_config']['kwargs'].update({key: value})
        return common

    def transform(self):
        """
        This method will do the transform operation to get a compatible
        openstack version 3 properties
        :return dict: Compatible openstack version 3 properties
        """
        return self.get_transformation_handler()[self._type]()
