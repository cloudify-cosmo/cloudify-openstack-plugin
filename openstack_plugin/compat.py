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
    'name',
    'ram',
    'disk',
    'vcpus'
)

AGGREGATE_RESOURCE_CONFIG = (
    'name',
    'availability_zone'
)

IMAGE_RESOURCE_CONFIG = (
    'name',
    'container_format',
    'disk_format',
    'tags'
)

KEYPAIR_RESOURCE_CONFIG = (
    'name',
    'public_key',
)

SERVER_GROUP_RESOURCE_CONFIG = (
    'name',
    'policies',
)

USER_RESOURCE_CONFIG = (
    'name',
    'default_project_id',
    'domain_id',
    'enabled',
    'password',
    'email'
)

PROJECT_RESOURCE_CONFIG = (
    'name',
    'description',
    'is_domain',
    'domain_id',
    'parent_id',
    'tags'
)

VOLUME_RESOURCE_CONFIG = (
    'name',
    'description',
    'project_id',
    'size',
    'availability_zone',
    'imageRef',
    'snapshot_id',
    'volume_type'
)


class Compat(object):
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
            'cloudify.openstack.nodes.Flavor': self._transform_flavor,
            'cloudify.openstack.nodes.HostAggregate':
                self._transform_aggregate,
            'cloudify.openstack.nodes.Image': self._transform_image,
            'cloudify.openstack.nodes.KeyPair': self._transform_keypair,
            'cloudify.openstack.nodes.ServerGroup':
                self._transform_server_group,
            'cloudify.openstack.nodes.User': self._transform_user,
            'cloudify.openstack.nodes.Project': self._transform_project,
            'cloudify.openstack.nodes.Volume': self._transform_volume
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
            client_config = dict()
            # Parse openstack config so that we can populate the client
            # config for the `client_config` object
            for key, value in self._properties['openstack_config'].items():
                client_config[key] = value
            common['client_config'] = client_config

        common['resource_config'] = dict()
        common['resource_config']['kwargs'] = dict()
        # Check if use external resource is set to "True" so that we can
        # update the resource config with external resource id
        if self._properties.get('resource_id'):
            if self._properties.get(USE_EXTERNAL_RESOURCE_PROPERTY):
                common['resource_config']['id'] = \
                    self._properties['resource_id']
            else:
                common['resource_config']['name'] = \
                    self._properties['resource_id']

        return common

    def _transform(self, openstack_type, resource_config_keys):
        """
        This method will transform old node properties to the new node
        properties based on the node type and resource config keys
        :param str openstack_type: Openstack object type.
        :param tuple resource_config_keys: Tuple of allowed keys defined under
        "resource_config" property for openstack nodes powered by version 3.x
        :return dict: Compatible node openstack version 3 properties
        """
        properties = self.get_common_properties()
        for key, value in self._properties.get(openstack_type, {}).items():
            if key in resource_config_keys:
                properties['resource_config'][key] = value
            else:
                properties['resource_config']['kwargs'].update({key: value})

        return properties

    def _transform_flavor(self):
        """
        This method will do transform operation for flavor node to be
        compatible with openstack flavor version 3
        :return dict: Compatible flavor openstack version 3 properties
        """
        return self._transform('flavor', FLAVOR_RESOURCE_CONFIG)

    def _transform_aggregate(self):
        """
        This method will do transform operation for aggregate node to be
        compatible with openstack aggregate version 3
        :return dict: Compatible aggregate openstack version 3 properties
        """
        return self._transform('aggregate', AGGREGATE_RESOURCE_CONFIG)

    def _transform_image(self):
        """
        This method will do transform operation for image node to be
        compatible with openstack image version 3
        :return dict: Compatible image openstack version 3 properties
        """
        return self._transform('image', IMAGE_RESOURCE_CONFIG)

    def _transform_keypair(self):
        """
        This method will do transform operation for keypair node to be
        compatible with openstack keypair version 3
        :return dict: Compatible keypair openstack version 3 properties
        """
        return self._transform('keypair', KEYPAIR_RESOURCE_CONFIG)

    def _transform_server_group(self):
        """
        This method will do transform operation for server group node to be
        compatible with openstack server group version 3
        :return dict: Compatible server group openstack version 3 properties
        """
        # This will populate both "client_config" & "resource_config" for
        # server group node
        sg_properties = self._transform('server_group',
                                        SERVER_GROUP_RESOURCE_CONFIG)
        # Server group openstack node 2.x contains other data which need to
        # be injected to the configuration when create server group
        if not sg_properties.get('policies') and \
                self._properties.get('policy'):
            sg_properties['resource_config']['policies'] = \
                [self._properties['policy']]
        return sg_properties

    def _transform_user(self):
        """
        This method will do transform operation for user node to be
        compatible with openstack user version 3
        :return dict: Compatible user openstack version 3 properties
        """
        return self._transform('user', USER_RESOURCE_CONFIG)

    def _transform_project(self):
        """
        This method will do transform operation for project node to be
        compatible with openstack project version 3
        :return dict: Compatible project openstack version 3 properties
        """
        return self._transform('project', PROJECT_RESOURCE_CONFIG)

    def _transform_volume(self):
        """
        This method will do transform operation for volume node to be
        compatible with openstack volume version 3
        :return dict: Compatible volume openstack version 3 properties
        """
        return self._transform('volume', VOLUME_RESOURCE_CONFIG)

    def transform(self):
        """
        This method will do the transform operation to get a compatible
        openstack version 3 properties based on the current node type
        :return dict: Compatible openstack version 3 properties
        """
        return self.get_transformation_handler()[self._type]()
