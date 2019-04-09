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
import copy

# Third party imports
import openstack.exceptions
from cloudify import ctx as _ctx

# Local imports
from openstack_plugin.constants import USE_EXTERNAL_RESOURCE_PROPERTY
from openstack_sdk.resources.compute import (OpenstackFlavor,
                                             OpenstackHostAggregate,
                                             OpenstackKeyPair,
                                             OpenstackServer,
                                             OpenstackServerGroup)

from openstack_sdk.resources.identity import (OpenstackUser,
                                              OpenstackProject)

from openstack_sdk.resources.networks import (OpenstackFloatingIP,
                                              OpenstackNetwork,
                                              OpenstackPort,
                                              OpenstackRBACPolicy,
                                              OpenstackRouter,
                                              OpenstackSecurityGroup,
                                              OpenstackSubnet)

from openstack_sdk.resources.volume import OpenstackVolume
from openstack_sdk.resources.images import OpenstackImage
from openstack_plugin.utils import get_target_node_from_capabilities

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

SECURITY_GROUP_RESOURCE_CONFIG = (
    'name',
    'description',
)

RBAC_POLICY_RESOURCE_CONFIG = (
    'target_tenant',
    'object_type',
    'object_id',
    'action'
)


class Compat(object):
    def __init__(self, context, **kwargs):
        """
        This will set current node context in order to help do the
        transformation process
        :param context: Cloudify context cloudify.context.CloudifyContext
        """
        self.context = context
        self.kwargs = kwargs
        self._properties = self.context.node.properties
        self._type = self.context.node.type

    @property
    def transformation_handler_map(self):
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
            'cloudify.openstack.nodes.Router': self._transform_router,
            'cloudify.openstack.nodes.SecurityGroup':
                self._transform_security_group,
            'cloudify.openstack.nodes.RBACPolicy': self._transform_rbac_policy
        }

    @property
    def resource_class_map(self):
        return {
            'flavor': OpenstackFlavor,
            'aggregate': OpenstackHostAggregate,
            'image': OpenstackImage,
            'keypair': OpenstackKeyPair,
            'server': OpenstackServer,
            'server_group': OpenstackServerGroup,
            'user': OpenstackUser,
            'project': OpenstackProject,
            'floatingip': OpenstackFloatingIP,
            'network': OpenstackNetwork,
            'port': OpenstackPort,
            'rbac_policy': OpenstackRBACPolicy,
            'router': OpenstackRouter,
            'security_group': OpenstackSecurityGroup,
            'subnet': OpenstackSubnet,
            'volume': OpenstackVolume
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
        return self.context.logger\
            if hasattr(self.context, 'logger') else _ctx.logger

    @property
    def has_server(self):
        return True if self._properties.get('server') else None

    @property
    def default_security_group_rule(self):
        """
        Property to return default security group rule
        :return dict: Return default rules
        """
        return {
            'direction': 'ingress',
            'ethertype': 'IPv4',
            'port_range_min': 1,
            'port_range_max': 65535,
            'protocol': 'tcp',
            'remote_group_id': None,
            'remote_ip_prefix': '0.0.0.0/0',
        }

    def get_openstack_resource_id(self,
                                  class_resource,
                                  resource_type,
                                  resource_name_or_id):
        """
        This method is used to lookup the resource id for openstack resource
        using openstack sdk api
        :param class_resource: Class of resource need to fetch resource id for
        :param resource_type: The resource type ("flavor" or "image") that we
        need to fetch
        resource id for
        :param resource_name_or_id: The name | id of the resource requested
        :return str: The uuid resource
        """
        resource = class_resource(client_config=self.openstack_config,
                                  logger=self.logger)
        remote_instance = \
            getattr(resource,
                    'find_{0}'.format(resource_type))(resource_name_or_id)
        if not remote_instance:
            raise openstack.exceptions.ResourceNotFound(
                'Resource {0} is not found'.format(resource_name_or_id))
        return remote_instance.id

    def get_common_properties(self, openstack_type):
        """
        This method will prepare common compatible openstack version 3
        properties
        :param str openstack_type: Openstack object type.
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
            resource_id = self._properties['resource_id']
            if self._properties.get(USE_EXTERNAL_RESOURCE_PROPERTY):
                # Get the class corresponding to the resource type provided
                class_resource = self.resource_class_map[openstack_type]
                # In the old plugin, resource_id could be a resource id or
                # could be a name, so before send that to the 3.x plugin we
                # should make sure that the plugin has the "id" translated
                # successfully according to the resource type
                resource_id = self.get_openstack_resource_id(class_resource,
                                                             openstack_type,
                                                             resource_id)
                common['resource_config']['id'] = resource_id
            else:
                common['resource_config']['name'] = \
                    self._properties['resource_id']

        return common

    def _process_security_group_rules(self):
        """
        This method will process and transform rules provided by user to
        the security group node so that, it can be compatible and
        consistent with openstack 3.x
        """
        if not self.kwargs.get('security_group_rules'):
            return

        rules = []
        sg_rule = copy.deepcopy(self.default_security_group_rule)
        for rule in self.kwargs['security_group_rules']:
            # Check if 'port' exists and then translate it
            if rule.get('port'):
                rule['port_range_min'] = rule['port']
                rule['port_range_max'] = rule['port']
                del rule['port']
            # Update rules
            sg_rule.update(rule)

            # Check if 'remote_group_id' exists, then we need to make sure
            # that 'remote_ip_prefix' is set to None because one of them
            # should only be set
            if sg_rule.get('remote_group_id'):
                sg_rule['remote_ip_prefix'] = None
            # Check if 'remote_group_node' is provided or not, then we need
            # to resolve the security group id from provided remote group
            # node name
            elif sg_rule.get('remote_group_node'):
                # lookup the remote group node in order to get the resource
                # id which is stored as runtime property
                _, remote_group_node = \
                    get_target_node_from_capabilities(
                        sg_rule['remote_group_node'])

                # Get the "external_id" for remote group node
                sg_rule['remote_group_id'] = \
                    remote_group_node.get('external_id')

                # Remove 'remote_group_node' because it is not longer needed
                del sg_rule['remote_group_node']
                # Set "remote_ip_prefix" since "remote_group_id" is set
                sg_rule['remote_ip_prefix'] = None
            # If the the name of the remote group is provided then we need
            # also to resolve it and update the "remote_group_id"
            elif sg_rule.get('remote_group_name'):
                sg_rule['remote_group_id'] =\
                    self.get_openstack_resource_id(
                        OpenstackSecurityGroup,
                        'security_group',
                        sg_rule['remote_group_name'])
                del sg_rule['remote_group_name']
                sg_rule['remote_ip_prefix'] = None

            rules.append(sg_rule)

        if rules:
            self.kwargs['security_group_rules'] = rules

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

    def _map_security_group_config(self):
        """
        This method will map the security group information to be
        consistent with openstack plugin 3.x
        """
        if self._properties.get('description'):
            self._properties['security_group']['description'] = \
                self._properties['description']

        # Map and process security group rules
        # "security_group_rules" is set from "rules" node property and
        # before we create/add rules to security group, we need to clean and
        # process them so that it can be consistent and matched openstack
        # plugin 3.x
        self._process_security_group_rules()

    def _transform(self, openstack_type, resource_config_keys):
        """
        This method will transform old node properties to the new node
        properties based on the node type and resource config keys
        :param str openstack_type: Openstack object type.
        :param tuple resource_config_keys: Tuple of allowed keys defined under
        "resource_config" property for openstack nodes powered by version 3.x
        :return dict: Compatible node openstack version 3 properties
        """
        properties = self.get_common_properties(openstack_type)
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

    def _transform_security_group(self):
        """
        This method will do transform operation for security group node to be
        compatible with openstack security group version 3
        :return dict: Compatible security group openstack version 3 properties
        """
        self._map_security_group_config()
        return self._transform('security_group',
                               SECURITY_GROUP_RESOURCE_CONFIG)

    def _transform_rbac_policy(self):
        """
        This method will do transform operation for rbac policy node to be
        compatible with openstack rbac policy version 3
        :return dict: Compatible rbac policy openstack version 3 properties
        """
        return self._transform('rbac_policy',
                               RBAC_POLICY_RESOURCE_CONFIG)

    def transform(self):
        """
        This method will do the transform operation to get a compatible
        openstack version 3 properties based on the current node type
        :return dict: Compatible openstack version 3 properties
        """
        properties = self.transformation_handler_map[self._type]()
        for key, value in properties.items():
            self.kwargs[key] = value
        return self.kwargs
