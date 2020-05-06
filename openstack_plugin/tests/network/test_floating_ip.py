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
import openstack.network.v2.floating_ip

# Local imports
from openstack_plugin.tests.base import OpenStackTestBase
from openstack_plugin.resources.network import floating_ip
from openstack_plugin.constants import (RESOURCE_ID,
                                        OPENSTACK_NAME_PROPERTY,
                                        OPENSTACK_TYPE_PROPERTY,
                                        FLOATING_IP_OPENSTACK_TYPE,
                                        NETWORK_OPENSTACK_TYPE,
                                        PORT_OPENSTACK_TYPE,
                                        SUBNET_OPENSTACK_TYPE,
                                        NETWORK_NODE_TYPE,
                                        PORT_NODE_TYPE,
                                        SUBNET_NODE_TYPE)


@mock.patch('openstack.connect')
class FloatingIPTestCase(OpenStackTestBase):

    def setUp(self):
        super(FloatingIPTestCase, self).setUp()

    @property
    def resource_config(self):
        return {
            'name': '10.0.0.1',
            'description': 'floating_ip_description',
        }

    def test_create(self, mock_connection):
        # Prepare the context for create operation
        rel_specs = [
            {
                'node': {
                    'id': 'network-1',
                    'properties': {
                        'client_config': self.client_config,
                        'resource_config': {
                            'name': 'test-network',
                        }
                    }
                },
                'instance': {
                    'id': 'network-1-efrgsd',
                    'runtime_properties': {
                        RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe8',
                        OPENSTACK_TYPE_PROPERTY: NETWORK_OPENSTACK_TYPE,
                        OPENSTACK_NAME_PROPERTY: 'test-network'
                    }
                },
                'type': NETWORK_NODE_TYPE,
            },
            {
                'node': {
                    'id': 'port-1',
                    'properties': {
                        'client_config': self.client_config,
                        'resource_config': {
                            'name': 'test-port',
                        }
                    }
                },
                'instance': {
                    'id': 'port-1-efrgsd',
                    'runtime_properties': {
                        RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe7',
                        OPENSTACK_TYPE_PROPERTY: PORT_OPENSTACK_TYPE,
                        OPENSTACK_NAME_PROPERTY: 'test-port'
                    }
                },
                'type': PORT_NODE_TYPE,
            },
            {
                'node': {
                    'id': 'subnet-1',
                    'properties': {
                        'client_config': self.client_config,
                        'resource_config': {
                            'name': 'test-subnet',
                        }
                    }
                },
                'instance': {
                    'id': 'subnet-1-efrgsd',
                    'runtime_properties': {
                        RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe6',
                        OPENSTACK_TYPE_PROPERTY: SUBNET_OPENSTACK_TYPE,
                        OPENSTACK_NAME_PROPERTY: 'test-subnet'
                    }
                },
                'type': SUBNET_NODE_TYPE,
            }
        ]

        floating_ip_rels = self.get_mock_relationship_ctx_for_node(rel_specs)
        self._prepare_context_for_operation(
            test_name='FloatingIPTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.create',
            test_relationships=floating_ip_rels)

        floating_ip_instance = openstack.network.v2.floating_ip.FloatingIP(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe4',
            'description': 'test_description',
            'name': '10.0.0.1',
            'created_at': '2016-03-09T12:14:57.233772',
            'fixed_ip_address': '',
            'floating_ip_address': '10.0.0.1',
            'floating_network_id': '3',
            'port_id': '5',
            'qos_policy_id': '51',
            'tenant_id': '6',
            'router_id': '7',
            'dns_domain': '9',
            'dns_name': '10',
            'status': 'ACTIVE',
            'revision_number': 12,
            'updated_at': '2016-07-09T12:14:57.233772',
            'subnet_id': '14',
            'tags': ['15', '16']

        })
        # Mock create floating ip response
        mock_connection().network.create_ip = \
            mock.MagicMock(return_value=floating_ip_instance)

        # Call create floating ip
        floating_ip.create(openstack_resource=None)

        self.assertEqual(self._ctx.instance.runtime_properties[RESOURCE_ID],
                         'a95b5509-c122-4c2f-823e-884bb559afe4')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY],
            '10.0.0.1')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY],
            FLOATING_IP_OPENSTACK_TYPE)

        self.assertEqual(
            self._ctx.instance.runtime_properties['floating_ip_address'],
            '10.0.0.1')

    def test_delete(self, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            test_name='FloatingIPTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.delete')

        floating_ip_instance = openstack.network.v2.floating_ip.FloatingIP(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe4',
            'description': 'test_description',
            'name': '10.0.0.1',
            'created_at': '2016-03-09T12:14:57.233772',
            'fixed_ip_address': '',
            'floating_ip_address': '10.0.0.1',
            'floating_network_id': '3',
            'port_id': '5',
            'qos_policy_id': '51',
            'tenant_id': '6',
            'router_id': '7',
            'dns_domain': '9',
            'dns_name': '10',
            'status': 'ACTIVE',
            'revision_number': 12,
            'updated_at': '2016-07-09T12:14:57.233772',
            'subnet_id': '14',
            'tags': ['15', '16']

        })
        # Mock delete floating ip response
        mock_connection().network.delete_ip = \
            mock.MagicMock(return_value=None)

        # Mock get floating ip response
        mock_connection().network.get_ip = \
            mock.MagicMock(return_value=floating_ip_instance)

        # Call delete floating ip
        floating_ip.delete(openstack_resource=None)

        for attr in [RESOURCE_ID,
                     OPENSTACK_NAME_PROPERTY,
                     OPENSTACK_TYPE_PROPERTY,
                     'floating_ip_address']:
            self.assertNotIn(attr, self._ctx.instance.runtime_properties)

    def test_update(self, mock_connection):
        # Prepare the context for update operation
        self._prepare_context_for_operation(
            test_name='FloatingIPTestCase',
            ctx_operation_name='cloudify.interfaces.operations.update')

        old_floating_ip_instance = \
            openstack.network.v2.floating_ip.FloatingIP(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe4',
                'description': 'test_description',
                'name': '10.0.0.1',
                'created_at': '2016-03-09T12:14:57.233772',
                'fixed_ip_address': '',
                'floating_ip_address': '10.0.0.1',
                'floating_network_id': '3',
                'port_id': '5',
                'qos_policy_id': '51',
                'tenant_id': '6',
                'router_id': '7',
                'dns_domain': '9',
                'dns_name': '10',
                'status': 'ACTIVE',
                'revision_number': 12,
                'updated_at': '2016-07-09T12:14:57.233772',
                'subnet_id': '14',
                'tags': ['15', '16']
            })

        new_config = {
            'port_id': '6',
        }

        new_floating_ip_instance = \
            openstack.network.v2.floating_ip.FloatingIP(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe4',
                'description': 'test_description',
                'name': '10.0.0.1',
                'created_at': '2016-03-09T12:14:57.233772',
                'fixed_ip_address': '',
                'floating_ip_address': '10.0.0.1',
                'floating_network_id': '3',
                'port_id': '6',
                'qos_policy_id': '51',
                'tenant_id': '6',
                'router_id': '7',
                'dns_domain': '9',
                'dns_name': '10',
                'status': 'ACTIVE',
                'revision_number': 12,
                'updated_at': '2016-07-09T12:14:57.233772',
                'subnet_id': '14',
                'tags': ['15', '16']
            })

        # Mock get floating ip response
        mock_connection().network.get_ip = \
            mock.MagicMock(return_value=old_floating_ip_instance)

        # Mock update floating ip response
        mock_connection().network.update_ip = \
            mock.MagicMock(return_value=new_floating_ip_instance)

        # Call update floating ip
        floating_ip.update(args=new_config,
                           openstack_resource=None)

    def test_list_floating_ips(self, mock_connection):
        # Prepare the context for list floating ips operation
        self._prepare_context_for_operation(
            test_name='FloatingIPTestCase',
            ctx_operation_name='cloudify.interfaces.operations.list')

        floating_ips = [
            openstack.network.v2.floating_ip.FloatingIP(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe4',
                'description': 'test_description',
                'name': '10.0.0.1',
                'created_at': '2016-03-09T12:14:57.233772',
                'fixed_ip_address': '',
                'floating_ip_address': '10.0.0.1',
                'floating_network_id': '3',
                'port_id': '5',
                'qos_policy_id': '51',
                'tenant_id': '6',
                'router_id': '7',
                'dns_domain': '9',
                'dns_name': '10',
                'status': 'ACTIVE',
                'revision_number': 12,
                'updated_at': '2016-07-09T12:14:57.233772',
                'subnet_id': '14',
                'tags': ['15', '16']
            }),
            openstack.network.v2.floating_ip.FloatingIP(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe3',
                'description': 'test_description_1',
                'name': '10.0.0.2',
                'created_at': '2016-03-09T12:14:57.233772',
                'fixed_ip_address': '',
                'floating_ip_address': '10.0.0.1',
                'floating_network_id': '3',
                'port_id': '6',
                'qos_policy_id': '51',
                'tenant_id': '6',
                'router_id': '7',
                'dns_domain': '9',
                'dns_name': '10',
                'status': 'ACTIVE',
                'revision_number': 12,
                'updated_at': '2016-08-09T12:14:57.233772',
                'subnet_id': '14',
                'tags': ['18', '17']
            }),
        ]

        # Mock list floating ip response
        mock_connection().network.ips = \
            mock.MagicMock(return_value=floating_ips)

        # Mock list floating ip response
        mock_connection().identity.find_project = \
            mock.MagicMock(return_value=self.project_resource)

        # Call list floating ips
        floating_ip.list_floating_ips(openstack_resource=None)

        # Check if the floating ips list saved as runtime properties
        self.assertIn(
            'floatingip_list',
            self._ctx.instance.runtime_properties)

        # Check the size of floating ips list
        self.assertEqual(
            len(self._ctx.instance.runtime_properties['floatingip_list']), 2)

    @mock.patch('openstack_sdk.common.OpenstackResource.get_quota_sets')
    def test_creation_validation(self, mock_quota_sets, mock_connection):
        # Prepare the context for creation validation operation
        self._prepare_context_for_operation(
            test_name='FloatingIPTestCase',
            ctx_operation_name='cloudify.interfaces.validation.creation')

        floating_ips = [
            openstack.network.v2.floating_ip.FloatingIP(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe4',
                'description': 'test_description',
                'name': '10.0.0.1',
                'created_at': '2016-03-09T12:14:57.233772',
                'fixed_ip_address': '',
                'floating_ip_address': '10.0.0.1',
                'floating_network_id': '3',
                'port_id': '5',
                'qos_policy_id': '51',
                'tenant_id': '6',
                'router_id': '7',
                'dns_domain': '9',
                'dns_name': '10',
                'status': 'ACTIVE',
                'revision_number': 12,
                'updated_at': '2016-07-09T12:14:57.233772',
                'subnet_id': '14',
                'tags': ['15', '16']
            }),
            openstack.network.v2.floating_ip.FloatingIP(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe3',
                'description': 'test_description_1',
                'name': '10.0.0.2',
                'created_at': '2016-03-09T12:14:57.233772',
                'fixed_ip_address': '',
                'floating_ip_address': '10.0.0.1',
                'floating_network_id': '3',
                'port_id': '6',
                'qos_policy_id': '51',
                'tenant_id': '6',
                'router_id': '7',
                'dns_domain': '9',
                'dns_name': '10',
                'status': 'ACTIVE',
                'revision_number': 12,
                'updated_at': '2016-08-09T12:14:57.233772',
                'subnet_id': '14',
                'tags': ['18', '17']
            }),
        ]

        # Mock list floating ip response
        mock_connection().network.ips = \
            mock.MagicMock(return_value=floating_ips)

        # Mock the quota size response
        mock_quota_sets.return_value = 20

        # Call creation validation
        floating_ip.creation_validation(openstack_resource=None)
