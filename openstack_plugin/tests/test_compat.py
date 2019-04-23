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

# Third party imports
import mock
import openstack.compute.v2.flavor
import openstack.image.v2.image
import openstack.identity.v3.project
import openstack.identity.v3.domain
import openstack.identity.v3.user
from cloudify.state import current_ctx

# Local imports
from openstack_plugin.tests.base import OpenStackTestBase
from openstack_sdk.resources import identity
from openstack_sdk.resources import compute
from openstack_sdk.resources import networks
from openstack_sdk.resources import volume
from openstack_sdk.resources import images
from openstack_plugin.compat import Compat
from openstack_plugin.compat import OLD_ROUTER_NODE
from openstack_plugin.constants import (CLOUDIFY_CREATE_OPERATION,
                                        CLOUDIFY_LIST_OPERATION,
                                        CLOUDIFY_UPDATE_OPERATION,
                                        CLOUDIFY_UPDATE_PROJECT_OPERATION)


class CompatTestCase(OpenStackTestBase):

    def setUp(self):
        super(CompatTestCase, self).setUp()

    @property
    def openstack_config(self):
        return {
            'auth_url': 'foo',
            'username': 'foo',
            'password': 'foo',
            'region_name': 'foo',
            'project_name': 'foo'
        }

    @property
    def node_properties(self):
        return {
            'openstack_config': self.openstack_config,
            'resource_id': 'test-resource',
            'use_external_resource': False
        }

    def test_init_compat_node(self):
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=self.node_properties,
        )
        compat_node = Compat(context=context, **{})
        self.assertIsNotNone(compat_node.logger)
        self.assertIsNotNone(compat_node.node_properties)
        self.assertIsNotNone(compat_node.openstack_config)

    def test_resource_class_map(self):
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=self.node_properties,
        )
        compat_node = Compat(context=context, **{})
        self.assertEqual(compat_node.resource_class_map['flavor'],
                         compute.OpenstackFlavor)
        self.assertEqual(compat_node.resource_class_map['aggregate'],
                         compute.OpenstackHostAggregate)
        self.assertEqual(compat_node.resource_class_map['image'],
                         images.OpenstackImage)
        self.assertEqual(compat_node.resource_class_map['keypair'],
                         compute.OpenstackKeyPair)
        self.assertEqual(compat_node.resource_class_map['server'],
                         compute.OpenstackServer)
        self.assertEqual(compat_node.resource_class_map['server_group'],
                         compute.OpenstackServerGroup)
        self.assertEqual(compat_node.resource_class_map['user'],
                         identity.OpenstackUser)
        self.assertEqual(compat_node.resource_class_map['project'],
                         identity.OpenstackProject)
        self.assertEqual(compat_node.resource_class_map['floatingip'],
                         networks.OpenstackFloatingIP)
        self.assertEqual(compat_node.resource_class_map['network'],
                         networks.OpenstackNetwork)
        self.assertEqual(compat_node.resource_class_map['port'],
                         networks.OpenstackPort)
        self.assertEqual(compat_node.resource_class_map['rbac_policy'],
                         networks.OpenstackRBACPolicy)
        self.assertEqual(compat_node.resource_class_map['router'],
                         networks.OpenstackRouter)
        self.assertEqual(compat_node.resource_class_map['security_group'],
                         networks.OpenstackSecurityGroup)
        self.assertEqual(compat_node.resource_class_map['subnet'],
                         networks.OpenstackSubnet)
        self.assertEqual(compat_node.resource_class_map['volume'],
                         volume.OpenstackVolume)

    def test_transformation_handler_map(self):
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=self.node_properties,
        )
        compat_node = Compat(context=context, **{})
        self.assertEqual(
            compat_node.transformation_handler_map[
                'cloudify.openstack.nodes.Flavor'
            ], compat_node._transform_flavor
        )
        self.assertEqual(
            compat_node.transformation_handler_map[
                'cloudify.openstack.nodes.HostAggregate'
            ], compat_node._transform_aggregate
        )
        self.assertEqual(
            compat_node.transformation_handler_map[
                'cloudify.openstack.nodes.Image'
            ], compat_node._transform_image
        )
        self.assertEqual(
            compat_node.transformation_handler_map[
                'cloudify.openstack.nodes.KeyPair'
            ], compat_node._transform_keypair
        )
        self.assertEqual(
            compat_node.transformation_handler_map[
                'cloudify.openstack.nodes.ServerGroup'
            ], compat_node._transform_server_group
        )
        self.assertEqual(
            compat_node.transformation_handler_map[
                'cloudify.openstack.nodes.User'
            ], compat_node._transform_user
        )
        self.assertEqual(
            compat_node.transformation_handler_map[
                'cloudify.openstack.nodes.Project'
            ], compat_node._transform_project
        )
        self.assertEqual(
            compat_node.transformation_handler_map[
                'cloudify.openstack.nodes.Volume'
            ], compat_node._transform_volume
        )
        self.assertEqual(
            compat_node.transformation_handler_map[
                'cloudify.openstack.nodes.Server'
            ], compat_node._transform_server
        )
        self.assertEqual(
            compat_node.transformation_handler_map[
                'cloudify.openstack.nodes.Network'
            ], compat_node._transform_network
        )
        self.assertEqual(
            compat_node.transformation_handler_map[
                'cloudify.openstack.nodes.Subnet'
            ], compat_node._transform_subnet
        )
        self.assertEqual(
            compat_node.transformation_handler_map[
                'cloudify.openstack.nodes.Port'
            ], compat_node._transform_port
        )
        self.assertEqual(
            compat_node.transformation_handler_map[
                'cloudify.openstack.nodes.FloatingIP'
            ], compat_node._transform_floating_ip
        )
        self.assertEqual(
            compat_node.transformation_handler_map[
                'cloudify.openstack.nodes.Router'
            ], compat_node._transform_router
        )
        self.assertEqual(
            compat_node.transformation_handler_map[
                'cloudify.openstack.nodes.Routes'
            ], compat_node._transform_routes
        )
        self.assertEqual(
            compat_node.transformation_handler_map[
                'cloudify.openstack.nodes.SecurityGroup'
            ], compat_node._transform_security_group
        )
        self.assertEqual(
            compat_node.transformation_handler_map[
                'cloudify.openstack.nodes.RBACPolicy'
            ], compat_node._transform_rbac_policy
        )

    def test_default_security_group_rule(self):
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=self.node_properties,
        )
        compat_node = Compat(context=context, **{})
        self.assertEqual(
            compat_node.default_security_group_rule,
            {
                'direction': 'ingress',
                'ethertype': 'IPv4',
                'port_range_min': 1,
                'port_range_max': 65535,
                'protocol': 'tcp',
                'remote_group_id': None,
                'remote_ip_prefix': '0.0.0.0/0',
            }
        )

    def test_operation_name(self):
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=self.node_properties,
            ctx_operation_name='foo_bar_test'
        )
        current_ctx.set(context)
        compat_node = Compat(context=context, **{})
        self.assertEqual(compat_node.operation_name, 'foo_bar_test')

    @mock.patch('openstack.connect')
    def test_get_openstack_resource_id(self, mock_connection):
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=self.node_properties,
        )
        compat_node = Compat(context=context, **{})
        flavor_instance = openstack.compute.v2.flavor.Flavor(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_flavor',
            'links': '2',
            'os-flavor-access:is_public': True,
            'ram': 6,
            'vcpus': 8,
            'swap': 8

        })
        # Mock find flavor response
        mock_connection().compute.find_flavor = \
            mock.MagicMock(return_value=flavor_instance)
        self.assertEqual(
            compat_node.get_openstack_resource_id(
                compute.OpenstackFlavor, 'flavor', 'test_flavor'),
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        )

    def test_populate_resource_id(self):
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=self.node_properties,
        )
        properties = dict()
        current_ctx.set(context)
        compat_node = Compat(context=context, **{})
        compat_node.populate_resource_id('flavor', properties)
        self.assertEqual(
            properties['resource_config']['name'], 'test-resource'
        )

    @mock.patch('openstack.connect')
    def test_populate_external_resource_id(self, mock_connection):
        node_properties = self.node_properties
        node_properties['use_external_resource'] = True
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
        )
        properties = dict()
        compat_node = Compat(context=context, **{})
        flavor_instance = openstack.compute.v2.flavor.Flavor(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_flavor',
            'links': '2',
            'os-flavor-access:is_public': True,
            'ram': 6,
            'vcpus': 8,
            'swap': 8

        })
        # Mock get flavor response
        mock_connection().compute.find_flavor = \
            mock.MagicMock(return_value=flavor_instance)
        compat_node.populate_resource_id('flavor', properties)
        self.assertEqual(
            properties['resource_config']['id'],
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        )

    def test_populate_openstack_config(self):
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=self.node_properties,
        )
        properties = dict()
        compat_node = Compat(context=context, **{})
        compat_node.populate_openstack_config(properties)
        self.assertEqual(properties['client_config'], self.openstack_config)

    def test_get_common_properties(self):
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=self.node_properties,
        )
        current_ctx.set(context)
        compat_node = Compat(context=context, **{})
        properties = compat_node.get_common_properties('flavor')
        self.assertEqual(properties['client_config'], self.openstack_config)
        self.assertEqual(
            properties['resource_config']['name'], 'test-resource'
        )

    def test_transform_create_flavor(self):
        node_properties = self.node_properties
        node_properties['flavor'] = {
            'vcpus': '4',
            'ram': '4096',
            'disk': '40',
        }

        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_CREATE_OPERATION,
            node_type='cloudify.openstack.nodes.Flavor'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                'swap': '0',
                'ephemeral': '0',
                'is_public': True
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(
            response['resource_config']['name'], 'test-resource'
        )
        self.assertEqual(
            response['resource_config']['kwargs']['swap'], '0'
        )
        self.assertEqual(
            response['resource_config']['kwargs']['ephemeral'], '0'
        )
        self.assertEqual(
            response['resource_config']['kwargs']['is_public'], True
        )

    def test_transform_list_flavor(self):
        node_properties = self.node_properties
        node_properties['flavor'] = {
            'vcpus': '4',
            'ram': '4096',
            'disk': '40',


        }

        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_LIST_OPERATION,
            node_type='cloudify.openstack.nodes.Flavor'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                'is_public': True,
                'min_disk': '40',
                'min_ram': '4096'
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(
            response['query'], {
                'is_public': True,
                'min_disk': '40',
                'min_ram': '4096'
            })
        self.assertNotIn('args', response)
        self.assertIn('client_config', response)
        self.assertIn('resource_config', response)

    def test_transform_create_aggregate(self):
        node_properties = self.node_properties
        node_properties['aggregate'] = {
            'name': 'test-name',
        }

        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_CREATE_OPERATION,
            node_type='cloudify.openstack.nodes.HostAggregate'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                'availability_zone': 'test-availability-zone'

            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(
            response['resource_config']['name'], 'test-name'
        )
        self.assertEqual(
            response['resource_config']['availability_zone'],
            'test-availability-zone'
        )

    def test_transform_create_image(self):
        node_properties = self.node_properties
        node_properties['image'] = {
            'name': 'test-name',
            'container_format': 'bare',
            'disk_format': 'qcow2',
        }

        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_CREATE_OPERATION,
            node_type='cloudify.openstack.nodes.Image'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                'tags': [
                    'tag-1',
                    'tag-2',
                    'tag-3'
                ]

            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(response['resource_config']['name'], 'test-name')
        self.assertEqual(len(response['resource_config']['tags']), 3)

    def test_transform_list_image(self):
        node_properties = self.node_properties
        node_properties['flavor'] = {
            'name': 'test-name',
            'container_format': 'bare',
            'disk_format': 'qcow2'
        }

        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_LIST_OPERATION,
            node_type='cloudify.openstack.nodes.Image'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                'visibility': True,
                'status': 'ACTIVE',
                'protected': False,
                'tag': 'tag-1'
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(
            response['query'], {
                'visibility': True,
                'status': 'ACTIVE',
                'protected': False,
                'tag': 'tag-1'
            })
        self.assertNotIn('args', response)
        self.assertIn('client_config', response)
        self.assertIn('resource_config', response)

    def test_transform_update_image(self):
        node_properties = self.node_properties
        node_properties['image'] = {
            'name': 'test-name',
            'container_format': 'bare',
            'disk_format': 'qcow2',
        }

        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_UPDATE_OPERATION,
            node_type='cloudify.openstack.nodes.Image'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                'image_id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'remove_props': ['prop_1', 'prop_2', 'prop_3'],
                'container_format': 'bare',
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(response['resource_config']['name'], 'test-name')
        self.assertEqual(
            response['args']['image'],
            'a95b5509-c122-4c2f-823e-884bb559afe7'
        )
        self.assertEqual(
            response['args']['container_format'],
            'bare'
        )
        self.assertNotIn('remove_props', response['args'])

    def test_transform_create_keypair(self):
        node_properties = self.node_properties
        node_properties['keypair'] = {
            'name': 'test-name',
            'public_key': 'test-public-key',
            'key_type': 'ssh',
            'user_id': 'test_user'
        }

        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_CREATE_OPERATION,
            node_type='cloudify.openstack.nodes.KeyPair'
        )
        current_ctx.set(context)
        kwargs = {
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(response['resource_config']['name'], 'test-name')
        self.assertNotIn('key_type', response['resource_config']['kwargs'])
        self.assertNotIn('user_id', response['resource_config']['kwargs'])

    def test_transform_list_keypair(self):
        node_properties = self.node_properties
        node_properties['keypair'] = {
            'name': 'test-name',
            'public_key': 'test-public-key',
            'key_type': 'ssh',
            'user_id': 'test_user'
        }

        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_LIST_OPERATION,
            node_type='cloudify.openstack.nodes.KeyPair'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                'user_id': 'test_user',
                'marker': '1',
                'limit': '20',
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertNotIn('query', response)
        self.assertNotIn('args', response)

    def test_transform_create_server_group(self):
        node_properties = self.node_properties
        node_properties['server_group'] = {
            'name': 'test-name'
        }
        node_properties['policy'] = 'test-policy'

        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_CREATE_OPERATION,
            node_type='cloudify.openstack.nodes.ServerGroup'
        )
        current_ctx.set(context)
        kwargs = {
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(response['resource_config']['name'], 'test-name')
        self.assertNotIn('policy', response['resource_config'])
        self.assertIn('policies', response['resource_config'])
        self.assertEqual(['test-policy'],
                         response['resource_config']['policies'])

    def test_transform_list_server_group(self):
        node_properties = self.node_properties
        node_properties['server_group'] = {
            'name': 'test-name'
        }
        node_properties['policy'] = 'test-policy'

        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_LIST_OPERATION,
            node_type='cloudify.openstack.nodes.ServerGroup'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                'all_projects': True,
                'limit': '30',
                'offset': '0'
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(
            response['query'], {
                'all_projects': True,
                'limit': '30',
                'marker': '0'
            })
        self.assertNotIn('args', response)

    @mock.patch('openstack.connect')
    def test_transform_create_server(self, mock_connection):
        node_properties = self.node_properties
        node_properties['server'] = {
            'name': 'test-name',
            'networks': [
                {
                   'net-id': 'a95b5509-c122-4c2f-823e-884bb559ada7'
                },
            ],
            'flavor': 'test_flavor',
            'image': 'test_image'
        }
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_CREATE_OPERATION,
            node_type='cloudify.openstack.nodes.Server'
        )

        flavor_instance = openstack.compute.v2.flavor.Flavor(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_flavor',
            'links': '2',
            'os-flavor-access:is_public': True,
            'ram': 6,
            'vcpus': 8,
            'swap': 8

        })
        # Mock get flavor response
        mock_connection().compute.find_flavor = \
            mock.MagicMock(return_value=flavor_instance)

        image_instance = openstack.image.v2.image.Image(**{
            'id': 'a95b5509-c122-4c2f-823e-884aa259afe8',
            'name': 'test_image',
            'container_format': 'test_bare',
            'disk_format': 'test_format',
            'checksum': '6d8f1c8cf05e1fbdc8b543fda1a9fa7f',
            'size': 258540032

        })
        # Mock get image response
        mock_connection().image.get_image = \
            mock.MagicMock(return_value=image_instance)

        current_ctx.set(context)
        kwargs = {
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(response['resource_config']['name'], 'test-name')
        self.assertEqual(
            response['resource_config']['networks'],
            [
                {
                   'uuid': 'a95b5509-c122-4c2f-823e-884bb559ada7'
                },
            ]
        )
        self.assertEqual(
            response['resource_config']['flavor_id'],
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        )
        self.assertEqual(
            response['resource_config']['image_id'],
            'a95b5509-c122-4c2f-823e-884aa259afe8'
        )

    @mock.patch('openstack.connect')
    def test_transform_list_server(self, mock_connection):
        node_properties = self.node_properties
        node_properties['server'] = {
            'name': 'test-name',
            'networks': [
                {
                   'net-id': 'a95b5509-c122-4c2f-823e-884bb559ada7'
                },
            ],
            'flavor': 'test_flavor',
            'image': 'test_image'
        }
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_LIST_OPERATION,
            node_type='cloudify.openstack.nodes.Server'
        )

        flavor_instance = openstack.compute.v2.flavor.Flavor(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_flavor',
            'links': '2',
            'os-flavor-access:is_public': True,
            'ram': 6,
            'vcpus': 8,
            'swap': 8

        })
        # Mock get flavor response
        mock_connection().compute.get_flavor = \
            mock.MagicMock(return_value=flavor_instance)

        image_instance = openstack.image.v2.image.Image(**{
            'id': 'a95b5509-c122-4c2f-823e-884aa259afe8',
            'name': 'test_image',
            'container_format': 'test_bare',
            'disk_format': 'test_format',
            'checksum': '6d8f1c8cf05e1fbdc8b543fda1a9fa7f',
            'size': 258540032

        })
        # Mock get image response
        mock_connection().image.get_image = \
            mock.MagicMock(return_value=image_instance)

        current_ctx.set(context)
        kwargs = {
            'args': {
                'search_opts': {
                    'name': 'test_server',
                    'status': 'ACTIVE',
                    'image': 'test_image',
                    'is_deleted': False
                },
                'detailed': True,
                'marker': '0',
                'limit': '20',
                'sort_dirs': ['test_sort_dir'],
                'sort_keys': ['test_sort_key']
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(response['resource_config']['name'], 'test-name')
        self.assertEqual(
            response['query'], {
                'name': 'test_server',
                'status': 'ACTIVE',
                'image': 'test_image',
                'is_deleted': False,
                'details': True,
                'marker': '0',
                'limit': '20',
            })
        self.assertNotIn('args', response)

    @mock.patch('openstack.connect')
    def test_transform_create_user(self, mock_connection):
        node_properties = self.node_properties
        node_properties['user'] = {
            'name': 'test-name',
            'domain': 'test_domain',
            'project': 'test_project',
            'password': 'test_password',
            'email': 'test@test.com'
        }

        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_CREATE_OPERATION,
            node_type='cloudify.openstack.nodes.User'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                'description': 'test_description',
                'enabled': True,
                'default_project': 'test_default_project'
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }

        project_instance = openstack.identity.v3.project.Project(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_default_project',
            'description': 'Testing Project',
            'domain_id': 'c84q3312-d233-5e3a-823e-884bb559afe8',
            'enabled': True,
            'is_domain': True,
            'links': ['test1', 'test2'],
            'parent_id': 'a63f2223-d233-5e3a-823e-773aa448dga7'

        })
        # Mock find project response
        mock_connection().identity.get_project = \
            mock.MagicMock(return_value=project_instance)

        domain_instance = openstack.identity.v3.domain.Domain(**{
            'id': 'c84q3312-d233-5e3a-823e-884bb559afe8',
            'name': 'test_domain',
            'description': 'Testing Domain',

        })
        # Mock find domain response
        mock_connection().identity.get_domain = \
            mock.MagicMock(return_value=domain_instance)

        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(response['resource_config']['name'], 'test-name')
        self.assertEqual(
            response['resource_config']['domain_id'],
            'c84q3312-d233-5e3a-823e-884bb559afe8'
        )
        self.assertEqual(
            response['resource_config']['default_project_id'],
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        )
        self.assertEqual(
            response['resource_config'], {
                'name': 'test-name',
                'domain_id': 'c84q3312-d233-5e3a-823e-884bb559afe8',
                'default_project_id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'password': 'test_password',
                'email': 'test@test.com',
                'enabled': True,
                'kwargs': {
                    'description': 'test_description'
                }
            }
        )
        self.assertNotIn('args', response)

    @mock.patch('openstack.connect')
    def test_transform_update_user(self, mock_connection):
        node_properties = self.node_properties
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_UPDATE_OPERATION,
            node_type='cloudify.openstack.nodes.User'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                # Pass user name in order to update the user
                'user': 'test_user',
                'name': 'test-name',
                # Domain is not allowed to update in openstack sdk
                'domain': 'test_domain',
                # project is not allowed to update in openstack sdk
                'project': 'test_project',
                'password': 'test_password',
                'email': 'test@test.com',
                'description': 'test_description',
                'enabled': True,
                'default_project': 'test_default_project'
            },
            'openstack_config': self.openstack_config
        }

        user_instance = openstack.identity.v3.user.User(**{
            'id': 'e86a6618-b233-9h1a-734d-773cc448bgq7',
            'name': 'test_user',
            'is_enabled': True,
            'email': 'test@test.com',

        })
        # Mock get user response
        mock_connection().identity.get_user = \
            mock.MagicMock(return_value=user_instance)

        project_instance = openstack.identity.v3.project.Project(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_default_project',
            'description': 'Testing Project',
            'domain_id': 'c84q3312-d233-5e3a-823e-884bb559afe8',
            'enabled': True,
            'is_domain': True,
            'links': ['test1', 'test2'],
            'parent_id': 'a63f2223-d233-5e3a-823e-773aa448dga7'

        })
        # Mock find project response
        mock_connection().identity.get_project = \
            mock.MagicMock(return_value=project_instance)

        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(
            response['args'], {
                'user': 'e86a6618-b233-9h1a-734d-773cc448bgq7',
                'name': 'test-name',
                'description': 'test_description',
                'default_project_id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'password': 'test_password',
                'email': 'test@test.com',
                'enabled': True,
            }
        )

    @mock.patch('openstack.connect')
    def test_transform_list_user(self, mock_connection):
        node_properties = self.node_properties
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_LIST_OPERATION,
            node_type='cloudify.openstack.nodes.User'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                'domain': 'test_domain',
                'limit': '0',
                'marker': '30',
                'name': 'test_name',
                'enabled': True,
            },
            'openstack_config': self.openstack_config
        }

        domain_instance = openstack.identity.v3.domain.Domain(**{
            'id': 'c84q3312-d233-5e3a-823e-884bb559afe8',
            'name': 'test_domain',
            'description': 'Testing Domain',

        })
        # Mock find domain response
        mock_connection().identity.get_domain = \
            mock.MagicMock(return_value=domain_instance)

        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(
            response['query'], {
                'domain_id': 'c84q3312-d233-5e3a-823e-884bb559afe8',
                'limit': '0',
                'marker': '30',
                'name': 'test_name',
                'enabled': True,
            })
        self.assertNotIn('args', response)

    @mock.patch('openstack.connect')
    def test_transform_create_project(self, mock_connection):
        node_properties = self.node_properties
        node_properties['project'] = {
            'name': 'test_name',
            'domain': 'test_domain',
            'parent': 'test_project_parent',
            'enabled': True,
            'tags': ['test-1', 'test-2']
        }

        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_CREATE_OPERATION,
            node_type='cloudify.openstack.nodes.Project'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                'is_domain': True,
                'description': 'test_description'
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }

        project_instance = openstack.identity.v3.project.Project(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_project_parent',
            'description': 'Testing Project',
            'domain_id': 'c84q3312-d233-5e3a-823e-884bb559afe8',
            'enabled': True,
            'is_domain': True,
            'links': ['test1', 'test2'],
            'parent_id': 'a63f2223-d233-5e3a-823e-773aa448dga7'

        })
        # Mock find project response
        mock_connection().identity.get_project = \
            mock.MagicMock(return_value=project_instance)

        domain_instance = openstack.identity.v3.domain.Domain(**{
            'id': 'c84q3312-d233-5e3a-823e-884bb559afe8',
            'name': 'test_domain',
            'description': 'Testing Domain',

        })
        # Mock find domain response
        mock_connection().identity.get_domain = \
            mock.MagicMock(return_value=domain_instance)

        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(response['resource_config']['name'], 'test_name')
        self.assertEqual(
            response['resource_config']['domain_id'],
            'c84q3312-d233-5e3a-823e-884bb559afe8'
        )
        self.assertEqual(
            response['resource_config']['parent_id'],
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        )
        self.assertEqual(
            response['resource_config']['kwargs']['enabled'], True
        )

    @mock.patch('openstack.connect')
    def test_transform_update_project(self, mock_connection):
        node_properties = self.node_properties
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_UPDATE_PROJECT_OPERATION,
            node_type='cloudify.openstack.nodes.Project'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                'project': 'test_project',
                'name': 'test_name',
                'domain': 'test_domain',
                'enabled': True,
                'tags': ['test-1', 'test-2']
            },
            'openstack_config': self.openstack_config
        }

        project_instance = openstack.identity.v3.project.Project(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_project',
            'description': 'Testing Project',
            'domain_id': 'c84q3312-d233-5e3a-823e-884bb559afe8',
            'enabled': True,
            'is_domain': True,
            'links': ['test1', 'test2'],
            'parent_id': 'a63f2223-d233-5e3a-823e-773aa448dga7'

        })

        # Mock find project response
        mock_connection().identity.get_project = \
            mock.MagicMock(return_value=project_instance)

        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(
            response['args'], {
                'project': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_name',
                'enabled': True,
                'tags': ['test-1', 'test-2']
            }
        )

    @mock.patch('openstack.connect')
    def test_transform_list_project(self, mock_connection):
        node_properties = self.node_properties
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_LIST_OPERATION,
            node_type='cloudify.openstack.nodes.Project'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                'domain': 'test_domain',
                'limit': '0',
                'marker': '30',
                'is_domain': True,
                'enabled': True,
            },
            'openstack_config': self.openstack_config
        }

        domain_instance = openstack.identity.v3.domain.Domain(**{
            'id': 'c84q3312-d233-5e3a-823e-884bb559afe8',
            'name': 'test_domain',
            'description': 'Testing Domain',

        })
        # Mock find domain response
        mock_connection().identity.get_domain = \
            mock.MagicMock(return_value=domain_instance)

        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(
            response['query']['domain_id'],
            'c84q3312-d233-5e3a-823e-884bb559afe8'
        )
        self.assertNotIn('args', response)

    def test_transform_create_volume(self):
        node_properties = self.node_properties
        node_properties['volume'] = {
            'name': 'test-name',
            'description': 'test_description',
            'size': '20',
            'project_id': 'c84q3312-d233-5e3a-823e-884bb555ba27',
            'availability_zone': 'test_availability_zone'
        }

        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_CREATE_OPERATION,
            node_type='cloudify.openstack.nodes.Volume'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                'source_volid': 'test_source_volid',
                'consistencygroup_id': 'test_consistencygroup_id'
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(response['resource_config']['name'], 'test-name')
        self.assertEqual(
            response['resource_config']['kwargs'], {
                'source_volid': 'test_source_volid',
                'consistencygroup_id': 'test_consistencygroup_id'
            }
        )
        expected_config = {
            'name': 'test-name',
            'description': 'test_description',
            'size': '20',
            'project_id': 'c84q3312-d233-5e3a-823e-884bb555ba27',
            'availability_zone': 'test_availability_zone',
            'kwargs': {
                'source_volid': 'test_source_volid',
                'consistencygroup_id': 'test_consistencygroup_id'
            }
        }
        for key, value in expected_config.items():
            self.assertEqual(value, response['resource_config'][key])

    def test_transform_list_volume(self):
        node_properties = self.node_properties

        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_LIST_OPERATION,
            node_type='cloudify.openstack.nodes.Volume'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                'limit': '20',
                'marker': '0',
                'project_id': 'c84q3312-d233-5e3a-823e-884bb555ba27'
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(
            response['query'], {
                'limit': '20',
                'marker': '0',
                'project_id': 'c84q3312-d233-5e3a-823e-884bb555ba27'
            }
        )

    def test_transform_create_network(self):
        node_properties = self.node_properties
        node_properties['network'] = {
            'name': 'test-name',
            'admin_state_up': True,
        }

        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_CREATE_OPERATION,
            node_type='cloudify.openstack.nodes.Network'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                'routing': {
                    'external': False
                }
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(response['resource_config']['name'], 'test-name')
        self.assertEqual(
            response['resource_config']['kwargs'], {
                'routing': {
                    'external': False
                }
            }
        )
        expected_config = {
            'name': 'test-name',
            'admin_state_up': True,
            'kwargs': {
                'routing': {
                    'external': False
                }
            }
        }
        for key, value in expected_config.items():
            self.assertEqual(value, response['resource_config'][key])

    def test_transform_list_network(self):
        node_properties = self.node_properties
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_LIST_OPERATION,
            node_type='cloudify.openstack.nodes.Network'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                # These two elements query are not supported by openstack sdk
                'retrieve_all': True,
                'page_reverse': True,
                'limit': '20',
                'marker': '0',
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(
            response['query'], {
                'limit': '20',
                'marker': '0',
            }
        )
        self.assertNotIn('args', response)

    def test_transform_create_subnet(self):
        node_properties = self.node_properties
        node_properties['subnet'] = {
            'name': 'test_name',
            'enable_dhcp': True,
            'network_id': 'c84q3312-d233-5e3a-823e-884bb555ba27',
            'dns_nameservers': ['8.8.8.4'],
        }

        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_CREATE_OPERATION,
            node_type='cloudify.openstack.nodes.Subnet'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                'ip_version': '4',
                'cidr': '10.0.0.0/24'
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(response['resource_config']['name'], 'test_name')
        expected_config = {
            'name': 'test_name',
            'enable_dhcp': True,
            'network_id': 'c84q3312-d233-5e3a-823e-884bb555ba27',
            'dns_nameservers': ['8.8.8.4'],
            'ip_version': '4',
            'cidr': '10.0.0.0/24'
        }
        for key, value in expected_config.items():
            self.assertEqual(value, response['resource_config'][key])

    def test_transform_list_subnet(self):
        node_properties = self.node_properties
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_LIST_OPERATION,
            node_type='cloudify.openstack.nodes.Subnet'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                # These two elements query are not supported by openstack sdk
                'retrieve_all': True,
                'page_reverse': True,
                'limit': '20',
                'marker': '0',
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(
            response['query'], {
                'limit': '20',
                'marker': '0',
            }
        )
        self.assertNotIn('args', response)

    def test_transform_create_port(self):
        node_properties = self.node_properties
        node_properties['port'] = {
            'name': 'test_name',
            'device_id': 'c84q3312-d233-5e3a-823e-884bb555sa12',
            'network_id': 'a12q3312-d233-5e3a-823e-884bb555sa12'
        }

        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_CREATE_OPERATION,
            node_type='cloudify.openstack.nodes.Port'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                'security_groups': [
                    'b13a4423-d233-5e3a-823e-884aa444sa12',
                    'a12q3312-d233-5e3a-823e-773gg555sa12'
                ]
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(response['resource_config']['name'], 'test_name')
        expected_config = {
            'name': 'test_name',
            'device_id': 'c84q3312-d233-5e3a-823e-884bb555sa12',
            'network_id': 'a12q3312-d233-5e3a-823e-884bb555sa12',
            'security_groups': [
                'b13a4423-d233-5e3a-823e-884aa444sa12',
                'a12q3312-d233-5e3a-823e-773gg555sa12'
            ]
        }
        for key, value in expected_config.items():
            self.assertEqual(value, response['resource_config'][key])

    def test_transform_list_port(self):
        node_properties = self.node_properties
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_LIST_OPERATION,
            node_type='cloudify.openstack.nodes.Port'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                # These two elements query are not supported by openstack sdk
                'retrieve_all': True,
                'page_reverse': True,
                'limit': '20',
                'marker': '0',
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(
            response['query'], {
                'limit': '20',
                'marker': '0',
            }
        )
        self.assertNotIn('args', response)

    def test_transform_create_floating_ip(self):
        node_properties = self.node_properties
        node_properties['floatingip'] = {
            'description': 'test_description',
            'floating_network_id': 'b13a4423-d233-5e3a-823e-884aa444sa12',
            'floating_network_name': 'test_floating_network_name',
        }

        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_CREATE_OPERATION,
            node_type='cloudify.openstack.nodes.FloatingIP'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                'port_id': 'a26g5534-d233-4g2v-712d-775bb333fb23'
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        expected_config = {
            'description': 'test_description',
            'floating_network_id': 'b13a4423-d233-5e3a-823e-884aa444sa12',
            'floating_network_name': 'test_floating_network_name',
            'port_id': 'a26g5534-d233-4g2v-712d-775bb333fb23'
        }
        for key, value in expected_config.items():
            self.assertEqual(value, response['resource_config'][key])

    def test_transform_list_floating_ip(self):
        node_properties = self.node_properties
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_LIST_OPERATION,
            node_type='cloudify.openstack.nodes.FloatingIP'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                # These two elements query are not supported by openstack sdk
                'retrieve_all': True,
                'page_reverse': True,
                'limit': '20',
                'marker': '0',
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(
            response['query'], {
                'limit': '20',
                'marker': '0',
            }
        )
        self.assertNotIn('args', response)

    def test_transform_create_router(self):
        node_properties = self.node_properties
        node_properties['router'] = {
            'name': 'test_name'
        }

        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_CREATE_OPERATION,
            node_type='cloudify.openstack.nodes.Router'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                'routes': [
                    {
                        'destination': '10.10.4.0/24',
                        'nexthop': '192.168.123.123'
                    }
                ]
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        expected_config = {
            'name': 'test_name',
            'kwargs': {
                'routes': [
                    {
                        'destination': '10.10.4.0/24',
                        'nexthop': '192.168.123.123'
                    }
                ]
            }
        }
        for key, value in expected_config.items():
            self.assertEqual(value, response['resource_config'][key])

    def test_transform_list_router(self):
        node_properties = self.node_properties
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_LIST_OPERATION,
            node_type='cloudify.openstack.nodes.Router'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                # These two elements query are not supported by openstack sdk
                'retrieve_all': True,
                'page_reverse': True,
                'limit': '20',
                'marker': '0',
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(
            response['query'], {
                'limit': '20',
                'marker': '0',
            }
        )
        self.assertNotIn('args', response)

    def test_transform_create_routes(self):
        node_properties = self.node_properties
        routes = {
            'destination': '10.10.4.0/24',
            'nexthop': '192.168.123.123'
        }
        node_properties['routes'] = [routes]

        rel_specs = [
            {
                'node': {
                    'id': 'router-1',
                    'properties': {
                        'openstack_config': self.openstack_config,
                        'router': {
                            'name': 'test-router',
                        }
                    }
                },
                'instance': {
                    'id': 'router-1-efrgsd',
                    'runtime_properties': {
                        'id': 'a95b5509-c122-4c2f-823e-884bb559afe4',
                        'external_id': 'a95b5509-c122-4c2f-823e-884bb559afe4',
                    }
                },
                'type_hierarchy': ['cloudify.nodes.Root', OLD_ROUTER_NODE],
            },
        ]

        routes_rel = self.get_mock_relationship_ctx_for_node(rel_specs)
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_CREATE_OPERATION,
            test_relationships=routes_rel,
            node_type='cloudify.openstack.nodes.Routes'

        )
        current_ctx.set(context)
        kwargs = {
            'args': {},
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        expected_config = {
            'routes': [routes],
        }
        for key, value in expected_config.items():
            self.assertEqual(value, response[key])

    def test_transform_create_security_group(self):
        node_properties = self.node_properties
        node_properties['security_group'] = {
            'name': 'test_name',
        }
        node_properties['description'] = 'test_description'

        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_CREATE_OPERATION,
            node_type='cloudify.openstack.nodes.SecurityGroup'
        )
        current_ctx.set(context)
        kwargs = {
            'security_group_rules': [
                {
                    'remote_ip_prefix': '0.0.0.0/0',
                    'port': '80',
                    'remote_group_id': 'a95b5509-c122-4c2f-823e-884bb559afe4'
                }
            ],
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        expected_sg_rules = {
            'remote_ip_prefix': None,
            'port_range_min': '80',
            'port_range_max': '80',
            'direction': 'ingress',
            'ethertype': 'IPv4',
            'protocol': 'tcp',
            'remote_group_id': 'a95b5509-c122-4c2f-823e-884bb559afe4'
        }
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(
            'test_description',
            response['resource_config']['description']
        )
        self.assertEqual(
            'test_name',
            response['resource_config']['name']
        )

        for key, value in expected_sg_rules.items():
            self.assertEqual(value, response['security_group_rules'][0][key])

    def test_transform_list_security_group(self):
        node_properties = self.node_properties
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_LIST_OPERATION,
            node_type='cloudify.openstack.nodes.SecurityGroup'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                # These two elements query are not supported by openstack sdk
                'retrieve_all': True,
                'page_reverse': True,
                'limit': '20',
                'marker': '0',
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(
            response['query'], {
                'limit': '20',
                'marker': '0',
            }
        )
        self.assertNotIn('args', response)

    def test_transform_create_rbacy_plicy(self):
        node_properties = self.node_properties
        node_properties['rbac_policy'] = {
            'target_tenant': 'test_target_tenant',
            'object_type': 'test_object_type',
            'object_id': 'test_object_id',
            'action': 'test_action'
        }

        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_CREATE_OPERATION,
            node_type='cloudify.openstack.nodes.RBACPolicy'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {},
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        expected_config = {
            'target_tenant': 'test_target_tenant',
            'object_type': 'test_object_type',
            'object_id': 'test_object_id',
            'action': 'test_action'
        }
        for key, value in expected_config.items():
            self.assertEqual(value, response['resource_config'][key])

    def test_transform_list_rbacy_plicy(self):
        node_properties = self.node_properties
        context = self.get_mock_ctx(
            test_name='CompatTestCase',
            test_properties=node_properties,
            ctx_operation_name=CLOUDIFY_LIST_OPERATION,
            node_type='cloudify.openstack.nodes.RBACPolicy'
        )
        current_ctx.set(context)
        kwargs = {
            'args': {
                # These two elements query are not supported by openstack sdk
                'retrieve_all': True,
                'page_reverse': True,
                'limit': '20',
                'marker': '0',
            },
            'resource_id': 'test-resource',
            'openstack_config': self.openstack_config
        }
        compat_node = Compat(context=context, **kwargs)
        response = compat_node.transform()
        self.assertEqual(response['client_config'], self.openstack_config)
        self.assertEqual(
            response['query'], {
                'limit': '20',
                'marker': '0',
            }
        )
        self.assertNotIn('args', response)
