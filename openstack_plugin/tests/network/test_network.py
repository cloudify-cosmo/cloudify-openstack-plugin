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
import openstack.network.v2.network

# Local imports
from openstack_plugin.tests.base import OpenStackTestBase
from openstack_plugin.resources.network import network
from openstack_plugin.constants import (RESOURCE_ID,
                                        OPENSTACK_NAME_PROPERTY,
                                        OPENSTACK_TYPE_PROPERTY,
                                        NETWORK_OPENSTACK_TYPE)


@mock.patch('openstack.connect')
class NetworkTestCase(OpenStackTestBase):

    def setUp(self):
        super(NetworkTestCase, self).setUp()

    @property
    def resource_config(self):
        return {
            'name': 'test_network',
            'description': 'network_description',
        }

    def test_create(self, mock_connection):
        # Prepare the context for create operation
        self._prepare_context_for_operation(
            test_name='NetworkTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.create')

        network_instance = openstack.network.v2.network.Network(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe4',
            'name': 'test_network',
            'admin_state_up': True,
            'availability_zone_hints': ['1', '2'],
            'availability_zones': ['3'],
            'external': True,
            'created_at': '2016-03-09T12:14:57.233772',
            'description': '4',
            'dns_domain': '5',
            'ipv4_address_scope': '6',
            'ipv6_address_scope': '7',
            'is_default': False,
            'mtu': 8,
            'port_security_enabled': True,
            'project_id': '10',
            'provider:network_type': '11',
            'provider:physical_network': '12',
            'provider:segmentation_id': '13',
            'qos_policy_id': '14',
            'revision_number': 15,
            'router:external': True,
            'segments': '16',
            'shared': True,
            'status': '17',
            'subnets': ['18', '19'],
            'updated_at': '2016-07-09T12:14:57.233772',
            'vlan_transparent': False,

        })
        # Mock create network response
        mock_connection().network.create_network = \
            mock.MagicMock(return_value=network_instance)

        # Call create network
        network.create(openstack_resource=None)

        self.assertEqual(self._ctx.instance.runtime_properties[RESOURCE_ID],
                         'a95b5509-c122-4c2f-823e-884bb559afe4')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY],
            'test_network')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY],
            NETWORK_OPENSTACK_TYPE)

    def test_delete(self, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            test_name='NetworkTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.delete')

        network_instance = openstack.network.v2.network.Network(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe4',
            'name': 'test_network',
            'admin_state_up': True,
            'availability_zone_hints': ['1', '2'],
            'availability_zones': ['3'],
            'external': True,
            'created_at': '2016-03-09T12:14:57.233772',
            'description': '4',
            'dns_domain': '5',
            'ipv4_address_scope': '6',
            'ipv6_address_scope': '7',
            'is_default': False,
            'mtu': 8,
            'port_security_enabled': True,
            'project_id': '10',
            'provider:network_type': '11',
            'provider:physical_network': '12',
            'provider:segmentation_id': '13',
            'qos_policy_id': '14',
            'revision_number': 15,
            'router:external': True,
            'segments': '16',
            'shared': True,
            'status': '17',
            'subnets': ['18', '19'],
            'updated_at': '2016-07-09T12:14:57.233772',
            'vlan_transparent': False,

        })
        # Mock delete network response
        mock_connection().network.delete_network = \
            mock.MagicMock(return_value=None)

        # Mock get network response
        mock_connection().network.get_network = \
            mock.MagicMock(return_value=network_instance)

        # Call delete network
        network.delete(openstack_resource=None)

        for attr in [RESOURCE_ID,
                     OPENSTACK_NAME_PROPERTY,
                     OPENSTACK_TYPE_PROPERTY]:
            self.assertNotIn(attr, self._ctx.instance.runtime_properties)

    def test_update(self, mock_connection):
        # Prepare the context for update operation
        self._prepare_context_for_operation(
            test_name='NetworkTestCase',
            ctx_operation_name='cloudify.interfaces.operations.update')

        old_network_instance = openstack.network.v2.network.Network(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe4',
            'name': 'test_network',
            'admin_state_up': True,
            'availability_zone_hints': ['1', '2'],
            'availability_zones': ['3'],
            'external': True,
            'created_at': '2016-03-09T12:14:57.233772',
            'description': '4',
            'dns_domain': '5',
            'ipv4_address_scope': '6',
            'ipv6_address_scope': '7',
            'is_default': False,
            'mtu': 8,
            'port_security_enabled': True,
            'project_id': '10',
            'provider:network_type': '11',
            'provider:physical_network': '12',
            'provider:segmentation_id': '13',
            'qos_policy_id': '14',
            'revision_number': 15,
            'router:external': True,
            'segments': '16',
            'shared': True,
            'status': '17',
            'subnets': ['18', '19'],
            'updated_at': '2016-07-09T12:14:57.233772',
            'vlan_transparent': False,
        })

        new_config = {
            'name': 'test_updated_network',
        }

        new_network_instance = openstack.network.v2.network.Network(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe4',
            'name': 'test_updated_network',
            'admin_state_up': True,
            'availability_zone_hints': ['1', '2'],
            'availability_zones': ['3'],
            'external': True,
            'created_at': '2016-03-09T12:14:57.233772',
            'description': '4',
            'dns_domain': '5',
            'ipv4_address_scope': '6',
            'ipv6_address_scope': '7',
            'is_default': False,
            'mtu': 8,
            'port_security_enabled': True,
            'project_id': '10',
            'provider:network_type': '11',
            'provider:physical_network': '12',
            'provider:segmentation_id': '13',
            'qos_policy_id': '14',
            'revision_number': 15,
            'router:external': True,
            'segments': '16',
            'shared': True,
            'status': '17',
            'subnets': ['18', '19'],
            'updated_at': '2016-07-09T12:14:57.233772',
            'vlan_transparent': False,

        })

        # Mock get network response
        mock_connection().network.get_network = \
            mock.MagicMock(return_value=old_network_instance)

        # Mock update network response
        mock_connection().network.update_network = \
            mock.MagicMock(return_value=new_network_instance)

        # Call update network
        network.update(args=new_config,
                       openstack_resource=None)

    def test_list_networks(self, mock_connection):
        # Prepare the context for list projects operation
        self._prepare_context_for_operation(
            test_name='NetworkTestCase',
            ctx_operation_name='cloudify.interfaces.operations.list')

        networks = [
            openstack.network.v2.network.Network(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe4',
                'name': 'test_network_1',
                'admin_state_up': True,
                'availability_zone_hints': ['1', '2'],
                'availability_zones': ['3'],
                'external': True,
                'created_at': '2016-03-09T12:14:57.233772',
                'description': '4',
                'dns_domain': '5',
                'ipv4_address_scope': '6',
                'ipv6_address_scope': '7',
                'is_default': False,
                'mtu': 8,
                'port_security_enabled': True,
                'project_id': '10',
                'provider:network_type': '11',
                'provider:physical_network': '12',
                'provider:segmentation_id': '13',
                'qos_policy_id': '14',
                'revision_number': 15,
                'router:external': True,
                'segments': '16',
                'shared': True,
                'status': '17',
                'subnets': ['18', '19'],
                'updated_at': '2016-07-09T12:14:57.233772',
                'vlan_transparent': False,
            }),
            openstack.network.v2.network.Network(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe3',
                'name': 'test_network_2',
                'admin_state_up': True,
                'availability_zone_hints': ['1', '2'],
                'availability_zones': ['3'],
                'external': True,
                'created_at': '2016-03-09T12:14:57.233772',
                'description': '4',
                'dns_domain': '5',
                'ipv4_address_scope': '6',
                'ipv6_address_scope': '7',
                'is_default': False,
                'mtu': 8,
                'port_security_enabled': True,
                'project_id': '10',
                'provider:network_type': '11',
                'provider:physical_network': '12',
                'provider:segmentation_id': '13',
                'qos_policy_id': '14',
                'revision_number': 15,
                'router:external': True,
                'segments': '16',
                'shared': True,
                'status': '17',
                'subnets': ['18', '19'],
                'updated_at': '2016-07-09T12:14:57.233772',
                'vlan_transparent': False,
            }),
        ]

        # Mock list networks response
        mock_connection().network.networks = \
            mock.MagicMock(return_value=networks)

        # Mock find project response
        mock_connection().identity.find_project = \
            mock.MagicMock(return_value=self.project_resource)

        # Call list networks
        network.list_networks(openstack_resource=None)

        # Check if the networks list saved as runtime properties
        self.assertIn(
            'network_list',
            self._ctx.instance.runtime_properties)

        # Check the size of networks list
        self.assertEqual(
            len(self._ctx.instance.runtime_properties['network_list']), 2)

    @mock.patch('openstack_sdk.common.OpenstackResource.get_quota_sets')
    def test_creation_validation(self, mock_quota_sets, mock_connection):
        # Prepare the context for creation validation operation
        self._prepare_context_for_operation(
            test_name='NetworkTestCase',
            ctx_operation_name='cloudify.interfaces.validation.creation')

        networks = [
            openstack.network.v2.network.Network(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe4',
                'name': 'test_network_1',
                'admin_state_up': True,
                'availability_zone_hints': ['1', '2'],
                'availability_zones': ['3'],
                'external': True,
                'created_at': '2016-03-09T12:14:57.233772',
                'description': '4',
                'dns_domain': '5',
                'ipv4_address_scope': '6',
                'ipv6_address_scope': '7',
                'is_default': False,
                'mtu': 8,
                'port_security_enabled': True,
                'project_id': '10',
                'provider:network_type': '11',
                'provider:physical_network': '12',
                'provider:segmentation_id': '13',
                'qos_policy_id': '14',
                'revision_number': 15,
                'router:external': True,
                'segments': '16',
                'shared': True,
                'status': '17',
                'subnets': ['18', '19'],
                'updated_at': '2016-07-09T12:14:57.233772',
                'vlan_transparent': False,
            }),
            openstack.network.v2.network.Network(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe3',
                'name': 'test_network_2',
                'admin_state_up': True,
                'availability_zone_hints': ['1', '2'],
                'availability_zones': ['3'],
                'external': True,
                'created_at': '2016-03-09T12:14:57.233772',
                'description': '4',
                'dns_domain': '5',
                'ipv4_address_scope': '6',
                'ipv6_address_scope': '7',
                'is_default': False,
                'mtu': 8,
                'port_security_enabled': True,
                'project_id': '10',
                'provider:network_type': '11',
                'provider:physical_network': '12',
                'provider:segmentation_id': '13',
                'qos_policy_id': '14',
                'revision_number': 15,
                'router:external': True,
                'segments': '16',
                'shared': True,
                'status': '17',
                'subnets': ['18', '19'],
                'updated_at': '2016-07-09T12:14:57.233772',
                'vlan_transparent': False,
            }),
        ]

        # Mock list networks response
        mock_connection().network.networks = \
            mock.MagicMock(return_value=networks)

        # Mock the quota size response
        mock_quota_sets.return_value = 20

        # Call creation validation
        network.creation_validation(openstack_resource=None)
