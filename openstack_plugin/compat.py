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

# Third party imports
from openstack_sdk.resources.compute import OpenstackFlavor
from openstack_sdk.resources.images import OpenstackImage

NETWORK_CONFIG_MAP = {
    'net-id': 'uuid',
    'port-id': 'port',
    'v4-fixed-ip': 'fixed_ip',
    'v6-fixed-ip': 'fixed_ip'
}

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

SERVER_RESOURCE_CONFIG = (
    'name',
    'description',
    'image_id',
    'flavor_id',
    'availability_zone',
    'user_data',
    'metadata',
    'security_groups',
    'networks',
    'key_name'
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

NETWORK_RESOURCE_CONFIG = (
    'name',
    'external',
    'admin_state_up',
)

SUBNET_RESOURCE_CONFIG = (
    'name',
    'enable_dhcp',
    'network_id',
    'dns_nameservers',
    'allocation_pools',
    'host_routes',
    'ip_version',
    'gateway_ip',
    'cidr',
    'prefixlen',
    'ipv6_address_mode',
    'ipv6_ra_mode'
)

PORT_RESOURCE_CONFIG = (
    'name',
    'allowed_address_pairs',
    'device_id',
    'device_owner',
    'fixed_ips',
    'network_id',
    'security_groups',
)

FLOATING_IP_RESOURCE_CONFIG = (
    'description',
    'floating_network_id',
    'floating_network_name',
    'fixed_ip_address',
    'floating_ip_address',
    'port_id',
    'subnet_id',
    'dns_domain',
    'dns_name',
)

ROUTER_RESOURCE_CONFIG = (
    'name',
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
            'cloudify.openstack.nodes.Volume': self._transform_volume,
            'cloudify.openstack.nodes.Server': self._transform_server,
            'cloudify.openstack.nodes.Network': self._transform_network,
            'cloudify.openstack.nodes.Subnet': self._transform_subnet,
            'cloudify.openstack.nodes.Port': self._transform_port,
            'cloudify.openstack.nodes.FloatingIP': self._transform_floating_ip,
            'cloudify.openstack.nodes.Router': self._transform_router
        }

    @property
    def openstack_config(self):
        """
        This is a property to get the openstack config used in order to
        authenticate with openstack API
        :return dict: Return configuration required to authenticate with
        openstack api
        """
        return self._properties.get('openstack_config')

    @property
    def logger(self):
        """
        Return an instance of cloudify context logger
        :return logger: Instance of cloudify logger
        """
        return self.context.logger

    @property
    def has_server(self):
        return True if self._properties.get('server') else None

    def get_openstack_resource_id(self,
                                  class_resource,
                                  resource_type,
                                  resource_name):
        """
        This method is used to lookup the resource id for openstack resource
        using openstack sdk api
        :param class_resource: Class of resource need to fetch resource id for
        :param resource_type: The resource type ("flavor" or "image") that we
        need to fetch
        resource id for
        :param resource_name: The name of the resource requested
        :return str: The uuid resource
        """
        resource = class_resource(client_config=self.openstack_config,
                                  logger=self.logger)
        remote_instance = \
            getattr(resource, 'find_{0}'.format(resource_type))(resource_name)
        return remote_instance.id

    def get_common_properties(self):
        """
        This method will prepare common compatible openstack version 3
        properties
        :return dict: Common Compatible openstack version 3 properties
        """
        common = dict()
        # Populate client config from openstack config
        if self.openstack_config:
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

    def _map_server_networks_config(self):
        """
        This method will do a mapping between the networks config for the
        server using openstack plugin 2.x so that it can works under
        openstack plugin 3.x
        """
        if self.has_server:
            for key, value in self._properties['server'].items():
                if key == 'networks' and value and isinstance(value, list):
                    networks = list()
                    for item in value:
                        if item and isinstance(item, dict):
                            item_net = dict()
                            for item_key, item_value in item.items():
                                map_key = NETWORK_CONFIG_MAP.get(item_key)
                                if map_key:
                                    item_net[map_key] = item_value
                                else:
                                    item_net[item_key] = item_value

                            networks.append(item_net)
                    # update the networks object to match the networks object
                    # used and accepted by openstack 3.x
                    self._properties['server']['networks'] = networks

    def _map_server_flavor_and_image(self):
        """
        This method will map the flavor and image information to be
        consistent with openstack plugin 3.x
        """
        if self.has_server:
            flavor = self._properties['server'].get('flavor')
            image = self._properties['server'].get('image')
            if flavor:
                flavor_id = \
                    self.get_openstack_resource_id(OpenstackFlavor,
                                                   'flavor',
                                                   flavor)
                self._properties['server']['flavor_id'] = flavor_id
                del self._properties['server']['flavor']
            if image:
                image_id = \
                    self.get_openstack_resource_id(OpenstackImage,
                                                   'image',
                                                   image)
                self._properties['server']['image_id'] = image_id or ''
                del self._properties['server']['image']

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

    def _transform_server(self):
        """
        This method will do transform operation for server node to be
        compatible with openstack server version 3
        :return dict: Compatible server openstack version 3 properties
        """
        # Do a conversion for networks object
        self._map_server_networks_config()
        # Do a conversion for flavor and image
        self._map_server_flavor_and_image()
        return self._transform('server', SERVER_RESOURCE_CONFIG)

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

    def _transform_network(self):
        """
        This method will do transform operation for network node to be
        compatible with openstack network version 3
        :return dict: Compatible network openstack version 3 properties
        """
        return self._transform('network', NETWORK_RESOURCE_CONFIG)

    def _transform_subnet(self):
        """
        This method will do transform operation for subnet node to be
        compatible with openstack subnet version 3
        :return dict: Compatible subnet openstack version 3 properties
        """
        return self._transform('subnet', SUBNET_RESOURCE_CONFIG)

    def _transform_port(self):
        """
        This method will do transform operation for port node to be
        compatible with openstack port version 3
        :return dict: Compatible port openstack version 3 properties
        """
        return self._transform('port', PORT_RESOURCE_CONFIG)

    def _transform_floating_ip(self):
        """
        This method will do transform operation for floating ip node to be
        compatible with openstack floating ip version 3
        :return dict: Compatible floating ip openstack version 3 properties
        """
        return self._transform('floatingip', FLOATING_IP_RESOURCE_CONFIG)

    def _transform_router(self):
        """
        This method will do transform operation for router node to be
        compatible with openstack router version 3
        :return dict: Compatible router openstack version 3 properties
        """
        return self._transform('router', ROUTER_RESOURCE_CONFIG)

    def transform(self):
        """
        This method will do the transform operation to get a compatible
        openstack version 3 properties based on the current node type
        :return dict: Compatible openstack version 3 properties
        """
        return self.get_transformation_handler()[self._type]()
