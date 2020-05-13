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
import openstack.network.v2.subnet
import openstack.network.v2.network

# Local imports
from openstack_plugin.tests.base import OpenStackTestBase
from openstack_plugin.resources.network import subnet
from openstack_plugin.constants import (RESOURCE_ID,
                                        OPENSTACK_NAME_PROPERTY,
                                        OPENSTACK_TYPE_PROPERTY,
                                        SUBNET_OPENSTACK_TYPE,
                                        NETWORK_OPENSTACK_TYPE,
                                        NETWORK_NODE_TYPE)


@mock.patch('openstack.connect')
class SubnetTestCase(OpenStackTestBase):

    def setUp(self):
        super(SubnetTestCase, self).setUp()

    @property
    def resource_config(self):
        return {
            'name': 'test_subnet',
            'description': 'subnet_description',
            'cidr': '10.0.0.0/24'
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
                        RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe4',
                        OPENSTACK_TYPE_PROPERTY: NETWORK_OPENSTACK_TYPE,
                        OPENSTACK_NAME_PROPERTY: 'test-network'
                    }
                },
                'type': NETWORK_NODE_TYPE,
            },
        ]

        subnet_rels = self.get_mock_relationship_ctx_for_node(rel_specs)
        self._prepare_context_for_operation(
            test_name='SubnetTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.create',
            test_relationships=subnet_rels)

        subnet_instance = openstack.network.v2.subnet.Subnet(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_subnet',
            'allocation_pools': [{'1': 1}],
            'cidr': '2',
            'created_at': '3',
            'description': '4',
            'dns_nameservers': ['5'],
            'enable_dhcp': True,
            'gateway_ip': '6',
            'host_routes': ['7'],
            'ip_version': 8,
            'ipv6_address_mode': '9',
            'ipv6_ra_mode': '10',
            'network_id': '12',
            'revision_number': 13,
            'segment_id': '14',
            'service_types': ['15'],
            'subnetpool_id': '16',
            'tenant_id': '17',
            'updated_at': '18',
            'use_default_subnetpool': True,
        })

        # Mock create subnet response
        mock_connection().network.create_subnet = \
            mock.MagicMock(return_value=subnet_instance)

        # Call create subnet
        subnet.create(openstack_resource=None)

        self.assertEqual(self._ctx.instance.runtime_properties[RESOURCE_ID],
                         'a95b5509-c122-4c2f-823e-884bb559afe8')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY],
            'test_subnet')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY],
            SUBNET_OPENSTACK_TYPE)

    def test_delete(self, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            test_name='SubnetTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.delete')

        subnet_instance = openstack.network.v2.subnet.Subnet(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_subnet',
            'allocation_pools': [{'1': 1}],
            'cidr': '2',
            'created_at': '3',
            'description': '4',
            'dns_nameservers': ['5'],
            'enable_dhcp': True,
            'gateway_ip': '6',
            'host_routes': ['7'],
            'ip_version': 8,
            'ipv6_address_mode': '9',
            'ipv6_ra_mode': '10',
            'network_id': '12',
            'revision_number': 13,
            'segment_id': '14',
            'service_types': ['15'],
            'subnetpool_id': '16',
            'tenant_id': '17',
            'updated_at': '18',
            'use_default_subnetpool': True,
        })
        # Mock delete subnet response
        mock_connection().network.delete_subnet = \
            mock.MagicMock(return_value=None)

        # Mock get subnet response
        mock_connection().network.get_subnet = \
            mock.MagicMock(return_value=subnet_instance)

        # Call delete subnet
        subnet.delete(openstack_resource=None)

        for attr in [RESOURCE_ID,
                     OPENSTACK_NAME_PROPERTY,
                     OPENSTACK_TYPE_PROPERTY]:
            self.assertNotIn(attr, self._ctx.instance.runtime_properties)

    def test_update(self, mock_connection):
        # Prepare the context for update operation
        self._prepare_context_for_operation(
            test_name='SubnetTestCase',
            ctx_operation_name='cloudify.interfaces.operations.update')

        old_subnet_instance = openstack.network.v2.subnet.Subnet(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_subnet',
            'allocation_pools': [{'1': 1}],
            'cidr': '2',
            'created_at': '3',
            'description': '4',
            'dns_nameservers': ['5'],
            'enable_dhcp': True,
            'gateway_ip': '6',
            'host_routes': ['7'],
            'ip_version': 8,
            'ipv6_address_mode': '9',
            'ipv6_ra_mode': '10',
            'network_id': '12',
            'revision_number': 13,
            'segment_id': '14',
            'service_types': ['15'],
            'subnetpool_id': '16',
            'tenant_id': '17',
            'updated_at': '18',
            'use_default_subnetpool': True,
        })

        new_config = {
            'name': 'test_updated_subnet',
        }

        new_subnets_instance = \
            openstack.network.v2.subnet.Subnet(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_updated_subnet',
                'allocation_pools': [{'1': 1}],
                'cidr': '2',
                'created_at': '3',
                'description': '4',
                'dns_nameservers': ['5'],
                'enable_dhcp': True,
                'gateway_ip': '6',
                'host_routes': ['7'],
                'ip_version': 8,
                'ipv6_address_mode': '9',
                'ipv6_ra_mode': '10',
                'network_id': '12',
                'revision_number': 13,
                'segment_id': '14',
                'service_types': ['15'],
                'subnetpool_id': '16',
                'tenant_id': '17',
                'updated_at': '18',
                'use_default_subnetpool': True,
            })

        # Mock get subnet response
        mock_connection().network.get_subnet = \
            mock.MagicMock(return_value=old_subnet_instance)

        # Mock update subnet response
        mock_connection().network.update_subnet = \
            mock.MagicMock(return_value=new_subnets_instance)

        # Call update subnet
        subnet.update(args=new_config,
                      openstack_resource=None)

    def test_list_subnets(self, mock_connection):
        # Prepare the context for list subnets operation
        self._prepare_context_for_operation(
            test_name='SubnetTestCase',
            ctx_operation_name='cloudify.interfaces.operations.list')

        subnets = [
            openstack.network.v2.subnet.Subnet(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_subnet_2',
                'allocation_pools': [{'1': 1}],
                'cidr': '2',
                'created_at': '3',
                'description': '4',
                'dns_nameservers': ['5'],
                'enable_dhcp': True,
                'gateway_ip': '6',
                'host_routes': ['7'],
                'ip_version': 8,
                'ipv6_address_mode': '9',
                'ipv6_ra_mode': '10',
                'network_id': '12',
                'revision_number': 13,
                'segment_id': '14',
                'service_types': ['15'],
                'subnetpool_id': '16',
                'tenant_id': '17',
                'updated_at': '18',
                'use_default_subnetpool': True,
            }),
            openstack.network.v2.subnet.Subnet(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe3',
                'name': 'test_subnet_2',
                'allocation_pools': [{'1': 1}],
                'cidr': '2',
                'created_at': '3',
                'description': '4',
                'dns_nameservers': ['5'],
                'enable_dhcp': True,
                'gateway_ip': '6',
                'host_routes': ['7'],
                'ip_version': 8,
                'ipv6_address_mode': '9',
                'ipv6_ra_mode': '10',
                'network_id': '12',
                'revision_number': 13,
                'segment_id': '14',
                'service_types': ['15'],
                'subnetpool_id': '16',
                'tenant_id': '17',
                'updated_at': '18',
                'use_default_subnetpool': True,
            }),
        ]

        # Mock list subnets response
        mock_connection().network.subnets = \
            mock.MagicMock(return_value=subnets)

        # Mock find project response
        mock_connection().identity.find_project = \
            mock.MagicMock(return_value=self.project_resource)

        # Call list subnets
        subnet.list_subnets(openstack_resource=None)

        # Check if the subnets list saved as runtime properties
        self.assertIn(
            'subnet_list',
            self._ctx.instance.runtime_properties)

        # Check the size of subnets list
        self.assertEqual(
            len(self._ctx.instance.runtime_properties['subnet_list']), 2)

    @mock.patch('openstack_sdk.common.OpenstackResource.get_quota_sets')
    def test_creation_validation(self, mock_quota_sets, mock_connection):
        # Prepare the context for creation validation operation
        self._prepare_context_for_operation(
            test_name='SubnetTestCase',
            ctx_operation_name='cloudify.interfaces.validation.creation')

        subnets = [
            openstack.network.v2.subnet.Subnet(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_subnet_2',
                'allocation_pools': [{'1': 1}],
                'cidr': '2',
                'created_at': '3',
                'description': '4',
                'dns_nameservers': ['5'],
                'enable_dhcp': True,
                'gateway_ip': '6',
                'host_routes': ['7'],
                'ip_version': 8,
                'ipv6_address_mode': '9',
                'ipv6_ra_mode': '10',
                'network_id': '12',
                'revision_number': 13,
                'segment_id': '14',
                'service_types': ['15'],
                'subnetpool_id': '16',
                'tenant_id': '17',
                'updated_at': '18',
                'use_default_subnetpool': True,
            }),
            openstack.network.v2.subnet.Subnet(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe3',
                'name': 'test_subnet_2',
                'allocation_pools': [{'1': 1}],
                'cidr': '2',
                'created_at': '3',
                'description': '4',
                'dns_nameservers': ['5'],
                'enable_dhcp': True,
                'gateway_ip': '6',
                'host_routes': ['7'],
                'ip_version': 8,
                'ipv6_address_mode': '9',
                'ipv6_ra_mode': '10',
                'network_id': '12',
                'revision_number': 13,
                'segment_id': '14',
                'service_types': ['15'],
                'subnetpool_id': '16',
                'tenant_id': '17',
                'updated_at': '18',
                'use_default_subnetpool': True,
            }),
        ]

        # Mock list subnets response
        mock_connection().network.subnets = \
            mock.MagicMock(return_value=subnets)

        # Mock the quota size response
        mock_quota_sets.return_value = 20

        # Call creation validation
        subnet.creation_validation(openstack_resource=None)
