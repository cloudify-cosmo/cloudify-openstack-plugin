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
from cloudify.state import current_ctx

# Local imports
from openstack_plugin.tests.base import OpenStackTestBase
from openstack_sdk.resources import identity
from openstack_sdk.resources import compute
from openstack_sdk.resources import networks
from openstack_sdk.resources import volume
from openstack_sdk.resources import images
from openstack_plugin.compat import Compat
from openstack_plugin.constants import (CLOUDIFY_CREATE_OPERATION,
                                        CLOUDIFY_LIST_OPERATION,
                                        CLOUDIFY_UPDATE_OPERATION)


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
        mock_connection().compute.get_flavor = \
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
        mock_connection().compute.get_flavor = \
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
