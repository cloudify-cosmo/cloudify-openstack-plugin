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
from cloudify.exceptions import NonRecoverableError
from cloudify import ctx as _ctx

# Local imports
from openstack_plugin.constants import USE_EXTERNAL_RESOURCE_PROPERTY
from openstack_sdk.resources.compute import (OpenstackFlavor,
                                             OpenstackHostAggregate,
                                             OpenstackKeyPair,
                                             OpenstackServer,
                                             OpenstackServerGroup)

from openstack_sdk.resources.identity import (OpenstackUser,
                                              OpenstackProject,
                                              OpenstackDomain)

from openstack_sdk.resources.networks import (OpenstackFloatingIP,
                                              OpenstackNetwork,
                                              OpenstackPort,
                                              OpenstackRBACPolicy,
                                              OpenstackRouter,
                                              OpenstackSecurityGroup,
                                              OpenstackSubnet)

from openstack_sdk.resources.volume import OpenstackVolume
from openstack_sdk.resources.images import OpenstackImage
from openstack_plugin.constants import (CLOUDIFY_CREATE_OPERATION,
                                        CLOUDIFY_LIST_OPERATION,
                                        CLOUDIFY_UPDATE_OPERATION,
                                        CLOUDIFY_UPDATE_PROJECT_OPERATION)
from openstack_plugin.utils import (get_target_node_from_capabilities,
                                    get_current_operation,
                                    find_relationship_by_node_type,
                                    remove_duplicates_items)

NETWORK_CONFIG_MAP = {
    'net-id': 'uuid',
    'port-id': 'port',
    'v4-fixed-ip': 'fixed_ip',
    'v6-fixed-ip': 'fixed_ip'
}

# The exposed configuration from cloudify node types under "resource_config"
# which allow to create openstack resource using 3.x

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

DEPRECATED_CLINE_CONFIG = (
    'nova_url',
    'neutron_url',
    'custom_configuration',
    'logging'
)

DEPRECATED_ARGS = (
    'start_retry_interval',
    'private_key_path',
    'status_attempts',
    'status_timeout'
)

OS_PARAMS_MAP = {
    'detailed': 'details',
    'offset': 'marker'
}

# List of params allowed by the Openstack SDK (openstack plugin 3.x) in
# order to list & filter resources
FLAVOR_LIST_PARAMS = (
   'limit',
   'marker',
   'is_public',
   'sort_key',
   'sort_dir',
   'min_disk',
   'min_ram'
)

SERVER_GROUP_LIST_PARAMS = (
    'all_projects',
    'limit',
    'marker'
)

IMAGE_LIST_PARAMS = (
    'limit',
    'marker',
    'name',
    'visibility',
    'member_status',
    'owner',
    'status',
    'size_min',
    'size_max',
    'protected',
    'is_hidden',
    'sort_key',
    'sort_dir',
    'sort',
    'tag',
    'created_at',
    'updated_at'
)

SERVER_LIST_PARAMS = (
    'limit',
    'marker',
    'image',
    'flavor',
    'name',
    'status',
    'host',
    'sort_key',
    'sort_dir',
    'reservation_id',
    'tags',
    'is_deleted',
    'ipv4_address',
    'ipv6_address',
    'changes_since',
    'all_projects',
)

USER_LIST_PARAMS = (
    'limit',
    'marker',
    'domain_id',
    'name',
    'password_expires_at',
    'enabled'
)

PROJECT_LIST_PARAMS = (
    'limit',
    'marker',
    'domain_id',
    'is_domain',
    'name',
    'parent_id',
    'tags',
    'any_tags',
    'not_tags',
    'not_any_tags'
)

VOLUME_LIST_PARAMS = (
    'limit',
    'marker',
    'name',
    'status',
    'project_id',
    'all_tenants',
)

# List of params allowed by the Openstack SDK (openstack plugin 3.x) in
# order to update/create resources

USER_COMMON_PARAMS = (
    'default_project_id',
    'enabled',
    'name',
    'description',
    'email',
    'password',
)

USER_UPDATE_PARAMS = USER_COMMON_PARAMS
USER_CREATE_PARAMS = ('domain_id',) + USER_COMMON_PARAMS

PROJECT_COMMON_PARAMS = (
    'name',
    'is_domain',
    'description',
    'domain_id',
    'enabled',
    'tags'
)

VOLUME_CREATE_PARAMS = (
    'name',
    'description',
    'size',
    'imageRef',
    'project_id',
    'multiattach',
    'availability_zone',
    'source_volid',
    'consistencygroup_id',
    'volume_type',
    'snapshot_id',
    'metadata',
    'scheduler_hints'
)

PROJECT_UPDATE_PARAMS = PROJECT_COMMON_PARAMS
PROJECT_CREATE_PARAMS = ('parent_id',) + PROJECT_COMMON_PARAMS

# Common params to ignore
KEYPAIR_PARAMS_TO_IGNORE = (
    'user_id',
    'marker',
    'limit'
)
# Map to link each openstack resource to allowed params supported by
# openstack plugin 3.x
RESOURCE_LIST_PARAMS_MAP = {
    'flavor': FLAVOR_LIST_PARAMS,
    'server_group': SERVER_GROUP_LIST_PARAMS,
    'image': IMAGE_LIST_PARAMS,
    'server': SERVER_LIST_PARAMS,
    'user': USER_LIST_PARAMS,
    'project': PROJECT_LIST_PARAMS,
    'volume': VOLUME_LIST_PARAMS
}

DEPRECATED_CONFIG = DEPRECATED_CLINE_CONFIG + DEPRECATED_ARGS

OLD_ROUTER_NODE = 'cloudify.openstack.nodes.Router'


class Compat(object):
    def __init__(self, context, **kwargs):
        """
        This will set current node context in order to help do the
        transformation process
        :param context: Cloudify context cloudify.context.CloudifyContext
        """
        self.context = context
        self.kwargs = kwargs
        self._type = self.context.node.type
        self._properties = dict(self.node_properties)

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
            'cloudify.openstack.nodes.Routes': self._transform_routes,
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
    def node_properties(self):
        return self.context.node.properties

    @property
    def logger(self):
        """
        Return an instance of cloudify context logger
        :return logger: Instance of cloudify logger
        """
        return self.context.logger\
            if hasattr(self.context, 'logger') else _ctx.logger

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

    @property
    def operation_name(self):
        return get_current_operation()

    @property
    def is_update_operation(self):
        return self.operation_name in [CLOUDIFY_UPDATE_OPERATION,
                                       CLOUDIFY_UPDATE_PROJECT_OPERATION]

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

    def populate_resource_id(self, openstack_type, properties):
        """
        This method will populate properties with resource_id based on
        openstack_type provided
        :param str openstack_type: Openstack object type.
        :param dict properties: Common Compatible openstack version 3
        properties
        """
        if 'resource_config' not in properties:
            properties['resource_config'] = dict()
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
                properties['resource_config']['id'] = resource_id
            else:
                if not self.is_update_operation:
                    properties['resource_config']['name'] = \
                        self._properties['resource_id']

    def populate_openstack_config(self, properties):
        """
        This method will prepare common compatible openstack version 3
        properties for openstack config, so that we can use it with
        openstack 3.x plugin
        :param dict properties: Common Compatible openstack version 3
        properties for client config
        """
        client_config = dict()
        if self.openstack_config:
            # Parse openstack config so that we can populate the client
            # config for the `client_config` object
            for key, value in self._properties['openstack_config'].items():
                client_config[key] = value
            properties['client_config'] = client_config

    def get_common_properties(self, openstack_type):
        """
        This method will prepare common compatible openstack version 3
        properties
        :param str openstack_type: Openstack object type.
        :return dict: Common Compatible openstack version 3 properties
        """
        common = dict()
        # Populate client config from openstack config
        self.populate_openstack_config(common)
        common['resource_config'] = dict()
        common['resource_config']['kwargs'] = dict()
        self.populate_resource_id(openstack_type, common)
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

    def _process_operation_inputs(self, openstack_type):
        """
        This method will process and the args provided via interface
        operations and try to merge them if possible to be compatible and
        consistent with plugin 3.x
        :param str openstack_type: Openstack object type.
        """
        # For all operations, old plugin allow to override the resource_id &
        # openstack_config via interface operations inputs, so these need to
        # handle and merge/update with the one provided using node properties
        openstack_config = self._properties.get('openstack_config', {})
        if self.kwargs.get('openstack_config'):
            op_config = self.kwargs.pop('openstack_config')
            openstack_config.update(op_config)

        if self.kwargs.get('resource_id'):
            self._properties['resource_id'] = self.kwargs.pop('resource_id')

        # Ignore any deprecated config
        for item in DEPRECATED_CONFIG:
            if self.kwargs.get(item):
                self.kwargs.pop(item)
            elif openstack_config.get(item):
                openstack_config.pop(item)

        if 'args' in self.kwargs and not self.kwargs['args']:
            del self.kwargs['args']

        if self.operation_name == CLOUDIFY_CREATE_OPERATION:
            self._process_create_operation_inputs(openstack_type)

        if self.kwargs.get('args'):
            if self.operation_name == CLOUDIFY_LIST_OPERATION:
                self._process_list_operation_inputs(openstack_type)
            elif self.is_update_operation:
                self._process_update_operation_inputs(openstack_type)

    def _process_create_operation_inputs(self, openstack_type):
        """
        This method will lookup the args provided from input opertaions and
        merge them with resource config
        """
        resource_config = self._properties.get(openstack_type, {})
        resource_config.update(copy.deepcopy(self.kwargs.get('args', {})))
        if self.kwargs.get('args'):
            del self.kwargs['args']
        if openstack_type == 'user':
            self._map_user_config(resource_config, USER_CREATE_PARAMS)
        elif openstack_type == 'project':
            self._map_project_config(resource_config, PROJECT_CREATE_PARAMS)
        elif openstack_type == 'volume':
            Compat._clean_resource_config(resource_config,
                                          VOLUME_CREATE_PARAMS)
        elif openstack_type == 'keypair':
            self._clean_resource_config(resource_config,
                                        KEYPAIR_RESOURCE_CONFIG)

    def _process_update_operation_inputs(self, openstack_type):
        """
        Openstack plugin 2.x only supports update operation for the
        following resources:
         - Project
         - User
         - Router
         - Aggregate
         - Image
         In order to have a successful update operation using openstack
         plugin 3.x, we need to do some mapping/filtering before do the
         actual update via openstack sdk
         :param str openstack_type: Openstack object type.
        """
        if openstack_type == 'aggregate':
            self.kwargs['args'] = self.kwargs.get('args').pop('aggregate', {})
        elif openstack_type == 'image':
            self._process_update_operation_inputs_for_image()
        elif openstack_type == 'user':
            self._process_update_operation_inputs_for_user()
        elif openstack_type == 'project':
            self._process_update_operation_inputs_for_project()

    def _process_update_operation_inputs_for_user(self):
        """
        This method will handle update operation inputs for user
        """
        args = self.kwargs.get('args', {})
        # Update domain is not allowed in update user
        args.pop('domain', None)
        self._map_user_config(args, USER_UPDATE_PARAMS)

    def _process_update_operation_inputs_for_project(self):
        """
        This method will handle update operation inputs for project
        """
        args = self.kwargs.get('args', {})
        # Update domain is not allowed in update project
        args.pop('domain', None)
        self._map_project_config(args, PROJECT_UPDATE_PARAMS)

    def _process_update_operation_inputs_for_image(self):
        """
        This method will handle update operation inputs for image
        """
        for key, value in self.kwargs['args'].items():
            if key == 'image_id':
                self.kwargs['args']['image'] = self.kwargs['args'].pop(key)
            elif key == 'remove_props':
                # image update does not support remove_props key
                self.kwargs['args'].pop('remove_props')

    def _process_list_operation_inputs(self, openstack_type):
        """
        This method will try to match and map list params used by openstack
        old plugin to be compatible and consistent with openstack plugin 3.x
        :param str openstack_type: Openstack object type.
        """
        if openstack_type == 'image' and self.kwargs['args'].get('filters'):
            filters = self.kwargs['args'].pop('filters')
            self.kwargs['args'].update(filters)
        elif openstack_type in ['server', 'volume']:
            search_opts = self.kwargs['args'].pop('search_opts', {})
            self.kwargs['args'].update(search_opts)
        elif openstack_type in ['user', 'project']:
            domain = self.kwargs['args'].pop('domain', None)
            if domain:
                domain_id = self.get_openstack_resource_id(OpenstackDomain,
                                                           'domain',
                                                           domain)
                self.kwargs['args']['domain_id'] = domain_id

        params = dict()
        for key, value in self.kwargs['args'].items():
            if RESOURCE_LIST_PARAMS_MAP.get(openstack_type):
                if key in RESOURCE_LIST_PARAMS_MAP[openstack_type]:
                    params[key] = value
                elif key in OS_PARAMS_MAP.keys():
                    params[OS_PARAMS_MAP[key]] = value
            else:
                # Keypair in openstack sdk does not support any query param
                # to list keypair resources, which means we cannot apply the
                # same query list to openstack sdk
                if openstack_type == 'keypair'\
                        and key in KEYPAIR_PARAMS_TO_IGNORE:
                    self.kwargs['args'].pop(key)
                # All neutron resource support these two params which are
                # not supported by openstack sdk, and they should be ignored
                elif key not in ['retrieve_all', 'page_reverse']:
                    params[key] = value
                else:
                    self.kwargs['args'].pop(key)
        if params:
            self.kwargs['query'] = params
        del self.kwargs['args']

    @staticmethod
    def _map_server_networks_config(config):
        """
        This method will do a mapping between the networks config for the
        server using openstack plugin 2.x so that it can works under
        openstack plugin 3.x
        """
        for key, value in config.items():
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
                config['networks'] = networks

    def _map_server_flavor_and_image(self, config):
        """
        This method will map the flavor and image information to be
        consistent with openstack plugin 3.x
        :param dict config: Resource configuration needed to create flavor
        or image
        """
        flavor = config.get('flavor')
        image = config.get('image')
        if flavor:
            flavor_id = \
                self.get_openstack_resource_id(OpenstackFlavor,
                                               'flavor',
                                               flavor)
            config['flavor_id'] = flavor_id
            del config['flavor']
        if image:
            image_id = \
                self.get_openstack_resource_id(OpenstackImage,
                                               'image',
                                               image)
            config['image_id'] = image_id or ''
            del config['image']

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

    def _map_user_config(self, config, allowed_params):
        """
        This method will map the user information to be
        consistent with openstack plugin 3.x
        :param dict config: Resource configuration needed to create/update user
        :param tuple allowed_params: Tuple of keys supported by openstack
        3.x to update/create user
        """
        for key, value in config.items():
            if key == 'user':
                user_id = self.get_openstack_resource_id(OpenstackUser,
                                                         'user',
                                                         value)
                config.pop('user')
                config['user'] = user_id
            elif key == 'domain':
                domain_id = self.get_openstack_resource_id(OpenstackDomain,
                                                           'domain',
                                                           value)
                config.pop('domain')
                config['domain_id'] = domain_id
            elif key == 'default_project':
                project_id = self.get_openstack_resource_id(OpenstackProject,
                                                            'project',
                                                            value)
                config.pop('default_project')
                config['default_project_id'] = project_id
            elif key not in allowed_params:
                config.pop(key)

    def _map_project_config(self, config, allowed_params):
        """
        This method will map the project information to be
        consistent with openstack plugin 3.x
        :param dict config: Resource configuration needed to update project
        :param tuple allowed_params: Tuple of keys supported by openstack
        3.x to update project
        """
        for key, value in config.items():
            if key == 'project':
                project_id = self.get_openstack_resource_id(OpenstackProject,
                                                            'project',
                                                            value)
                config.pop('project')
                config['project'] = project_id
            elif key == 'parent':
                parent_id = self.get_openstack_resource_id(OpenstackProject,
                                                           'project',
                                                           value)
                config.pop('parent')
                config['parent_id'] = parent_id
            elif key == 'domain':
                domain_id = self.get_openstack_resource_id(OpenstackDomain,
                                                           'domain',
                                                           value)
                config.pop('domain')
                config['domain_id'] = domain_id
            elif key not in allowed_params:
                config.pop(key)

    @staticmethod
    def _clean_resource_config(config, allowed_params):
        """
        This method will clean the resource config from unsupported
        configuration that does not support by openstack plugin 3.x
        :param dict config: Resource configuration needed to create resource
        :param tuple allowed_params: Tuple of keys supported by openstack
        3.x to create resource
        """
        for key in config.keys():
            if key not in allowed_params:
                config.pop(key)

    def _transform(self, openstack_type, resource_config_keys):
        """
        This method will transform old node properties to the new node
        properties based on the node type and resource config keys
        :param str openstack_type: Openstack object type.
        :param tuple resource_config_keys: Tuple of allowed keys defined under
        "resource_config" property for openstack nodes powered by version 3.x
        :return dict: Compatible node openstack version 3 properties
        """
        self._process_operation_inputs(openstack_type)
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
        # self._process_keypair_config()
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
        server_config = self._properties.get('server', {})
        args_config = self.kwargs.get('args', {})
        for config in [server_config, args_config]:
            # Do a conversion for networks object
            Compat._map_server_networks_config(config)
            # Do a conversion for flavor and image
            self._map_server_flavor_and_image(config)

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

    def _transform_routes(self):
        """
        This method will do transform operation for routes node to be
        compatible with openstack routes version 3
        :return dict: Compatible routes openstack version 3 properties
        """
        properties = dict()
        self.populate_openstack_config(properties)
        router_id = None
        rel_router = find_relationship_by_node_type(self.context.instance,
                                                    OLD_ROUTER_NODE)
        if rel_router:
            router_instance = rel_router.target.instance
            router_id = \
                router_instance.runtime_properties.get('id') or \
                router_instance.runtime_properties.get('external_id')
        else:
            self.populate_resource_id('router', properties)
            router_id = properties['resource_config'].get('id')
            router_name = properties['resource_config'].get('name')
            if not (router_id or router_name):
                raise NonRecoverableError('Unable to transform routes node '
                                          'because router id is not missing')
            if not router_id:
                router_id = self.get_openstack_resource_id(
                    OpenstackRouter,
                    'router',
                    properties['resource_config']['name'])

        # Set runtime for node routes
        self.context.instance.runtime_properties['id'] = router_id
        self.context.instance.runtime_properties['external_id'] = router_id
        # Get routes data from node properties
        # and args via input operations
        routes = self._properties.get('routes', {})
        routes = remove_duplicates_items(routes)
        # Remove args from kwargs
        if 'args' in self.kwargs:
            del self.kwargs['args']
        if self.operation_name == CLOUDIFY_CREATE_OPERATION:
            properties['routes'] = routes
        return properties

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
