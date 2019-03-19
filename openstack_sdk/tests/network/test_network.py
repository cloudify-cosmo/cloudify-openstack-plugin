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
import mock

# Third party imports
import openstack.network.v2.network

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import networks


class NetworkTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(NetworkTestCase, self).setUp()
        self.fake_client = self.generate_fake_openstack_connection('network')
        self.network_instance = networks.OpenstackNetwork(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.network_instance.connection = self.connection

    def test_get_network(self):
        net = openstack.network.v2.network.Network(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
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
        self.network_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_network = mock.MagicMock(return_value=net)

        response = self.network_instance.get()
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.name, 'test_network')
        self.assertEqual(response.is_router_external, True)

    def test_list_networks(self):
        nets = [
            openstack.network.v2.network.Network(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_network_1',
                'description': 'test_description_1',
                'admin_state_up': True,
                'availability_zone_hints': ['1', '2'],
                'availability_zones': ['3'],
                'external': True,
                'created_at': '2016-03-09T12:14:57.233772',
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
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': 'test_network_2',
                'description': 'test_description_2',
                'admin_state_up': True,
                'availability_zone_hints': ['1', '2'],
                'availability_zones': ['3'],
                'external': True,
                'created_at': '2016-03-09T12:14:57.233772',
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
        ]

        self.fake_client.networks = mock.MagicMock(return_value=nets)
        response = self.network_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_network(self):
        net = {
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_network',
            'description': 'test_description',
            'admin_state_up': True,
            'availability_zone_hints': ['1', '2'],
            'availability_zones': ['3'],
            'project_id': '10',
        }

        new_res = openstack.network.v2.network.Network(**net)
        self.network_instance.config = net
        self.fake_client.create_network = mock.MagicMock(return_value=new_res)

        response = self.network_instance.create()
        self.assertEqual(response.name, net['name'])
        self.assertEqual(response.description, net['description'])

    def test_update_network(self):
        old_network = openstack.network.v2.network.Network(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_network',
            'description': 'test_description',
            'admin_state_up': True,
            'availability_zone_hints': ['1', '2'],
            'availability_zones': ['3'],
            'external': True,
            'created_at': '2016-03-09T12:14:57.233772',
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
            'name': 'test_network_updated',
            'description': 'test_description_updated',
            'mtu': 10,
            'admin_state_up': False,
        }

        new_network = openstack.network.v2.network.Network(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_network_updated',
            'description': 'test_description_updated',
            'admin_state_up': False,
            'availability_zone_hints': ['1', '2'],
            'availability_zones': ['3'],
            'external': True,
            'created_at': '2016-03-09T12:14:57.233772',
            'dns_domain': '5',
            'ipv4_address_scope': '6',
            'ipv6_address_scope': '7',
            'is_default': False,
            'mtu': 10,
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

        self.network_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_network = mock.MagicMock(return_value=old_network)
        self.fake_client.update_network = \
            mock.MagicMock(return_value=new_network)

        response = self.network_instance.update(new_config=new_config)
        self.assertNotEqual(response.name, old_network.name)
        self.assertNotEqual(response.description, old_network.description)
        self.assertNotEqual(response.mtu, old_network.mtu)
        self.assertNotEqual(response.is_admin_state_up,
                            old_network.is_admin_state_up)

    def test_delete_network(self):
        net = openstack.network.v2.network.Network(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_network',
            'description': 'test_description',
            'admin_state_up': True,
            'availability_zone_hints': ['1', '2'],
            'availability_zones': ['3'],
            'external': True,
            'created_at': '2016-03-09T12:14:57.233772',
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

        self.network_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_network = mock.MagicMock(return_value=net)
        self.fake_client.delete_network = mock.MagicMock(return_value=None)

        response = self.network_instance.delete()
        self.assertIsNone(response)
