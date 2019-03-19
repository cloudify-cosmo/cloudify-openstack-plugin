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
import openstack.network.v2.port

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import networks


class PortTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(PortTestCase, self).setUp()
        self.fake_client = self.generate_fake_openstack_connection('port')
        self.port_instance = networks.OpenstackPort(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.port_instance.connection = self.connection

    def test_get_port(self):
        port = openstack.network.v2.port.Port(**{
            'id': '1',
            'name': 'test_port',
            'admin_state_up': True,
            'binding_host_id': '3',
            'binding_profile': {'4': 4},
            'binding_vif_details': {'5': 5},
            'binding_vif_type': '6',
            'binding_vnic_type': '7',
            'created_at': '2016-03-09T12:14:57.233772',
            'data_plane_status': '32',
            'description': '8',
            'device_id': '9',
            'device_owner': '10',
            'dns_assignment': [{'11': '11'}],
            'dns_domain': 'a11',
            'dns_name': '12',
            'extra_dhcp_opts': [{'13': '13'}],
            'fixed_ips': [{'10.0.0.1': '10.0.0.2'}],
            'allowed_address_pairs': ['10.0.0.3', '10.0.0.4'],
            'mac_address': '00-14-22-01-23-45',
            'network_id': '18',
            'port_security_enabled': True,
            'qos_policy_id': '21',
            'revision_number': '22',
            'security_groups': ['23'],
            'status': '25',
            'tenant_id': '26',
            'updated_at': '2016-07-09T12:14:57.233772',
        })
        self.port_instance.resource_id = '1'
        self.fake_client.get_port = mock.MagicMock(return_value=port)

        response = self.port_instance.get()
        self.assertEqual(response.id, '1')
        self.assertEqual(response.name, 'test_port')
        self.assertEqual(response.is_admin_state_up, True)
        self.assertEqual(response.binding_host_id, '3')
        self.assertEqual(response.binding_profile, {'4': 4})

    def test_list_ports(self):
        ports = [
            openstack.network.v2.port.Port(**{
                'id': '1',
                'name': 'test_port_1',
                'description': 'test_port_description_1',
                'admin_state_up': True,
                'binding_host_id': '3',
                'binding_profile': {'4': 4},
                'binding_vif_details': {'5': 5},
                'binding_vif_type': '6',
                'binding_vnic_type': '7',
                'created_at': '2016-03-09T12:14:57.233772',
                'data_plane_status': '32',
                'device_id': '9',
                'device_owner': '10',
                'dns_assignment': [{'11': 11}],
                'dns_domain': 'a11',
                'dns_name': '12',
                'extra_dhcp_opts': [{'13': 13}],
                'fixed_ips': [{'10.0.0.1': '10.0.0.2'}],
                'allowed_address_pairs': ['10.0.0.3', '10.0.0.4'],
                'mac_address': '00-14-22-01-23-45',
                'network_id': '18',
                'port_security_enabled': True,
                'qos_policy_id': '21',
                'revision_number': 22,
                'security_groups': ['23'],
                'status': '25',
                'tenant_id': '26',
                'updated_at': '2016-07-09T12:14:57.233772',

            }),
            openstack.network.v2.port.Port(**{
                'id': '2',
                'name': 'test_port_2',
                'description': 'test_port_description_2',
                'admin_state_up': True,
                'binding_host_id': '3',
                'binding_profile': {'4': 4},
                'binding_vif_details': {'5': 5},
                'binding_vif_type': '6',
                'binding_vnic_type': '7',
                'created_at': '2016-03-09T12:14:57.233772',
                'data_plane_status': '32',
                'device_id': '9',
                'device_owner': '10',
                'dns_assignment': [{'11': '11'}],
                'dns_domain': 'a11',
                'dns_name': '12',
                'extra_dhcp_opts': [{'13': '13'}],
                'fixed_ips': [{'10.0.0.5': '10.0.0.6'}],
                'allowed_address_pairs': ['10.0.0.7', '10.0.0.9'],
                'mac_address': '00-14-22-01-23-45',
                'network_id': '18',
                'port_security_enabled': True,
                'qos_policy_id': '21',
                'revision_number': 22,
                'security_groups': ['23'],
                'status': '25',
                'tenant_id': '26',
                'updated_at': '2016-07-09T12:14:57.233772',

            })
        ]

        self.fake_client.ports = mock.MagicMock(return_value=ports)
        response = self.port_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_port(self):
        port = {
            'name': 'test_port',
            'admin_state_up': True,
            'description': 'test_port_description',
            'device_id': '9',
            'device_owner': '10',
            'dns_assignment': [{'11': '11'}],
            'dns_domain': 'a11',
            'dns_name': '12',
            'extra_dhcp_opts': [{'13': '13'}],
            'fixed_ips': [{'10.0.0.1': '10.0.0.2'}],
            'allowed_address_pairs': ['10.0.0.3', '10.0.0.4'],
            'mac_address': '00-14-22-01-23-45',
            'network_id': '18',
            'port_security_enabled': True,
            'qos_policy_id': '21',
            'security_groups': ['23'],
            'tenant_id': '26',
        }

        new_res = openstack.network.v2.port.Port(**port)
        self.port_instance.config = port
        self.fake_client.create_port = mock.MagicMock(return_value=new_res)

        response = self.port_instance.create()
        self.assertEqual(response.name, port['name'])
        self.assertEqual(response.description, port['description'])

    def test_update_port(self):
        old_port = openstack.network.v2.port.Port(**{
            'id': '1',
            'name': 'test_port',
            'description': 'test_port_description',
            'admin_state_up': True,
            'binding_host_id': '3',
            'binding_profile': {'4': '4'},
            'binding_vif_details': {'5': '5'},
            'binding_vif_type': '6',
            'binding_vnic_type': '7',
            'created_at': '2016-03-09T12:14:57.233772',
            'data_plane_status': '32',
            'device_id': '9',
            'device_owner': '10',
            'dns_assignment': [{'11': 11}],
            'dns_domain': 'a11',
            'dns_name': '12',
            'extra_dhcp_opts': [{'13': '13'}],
            'fixed_ips': [{'10.0.0.1': '10.0.0.2'}],
            'allowed_address_pairs': ['10.0.0.3', '10.0.0.4'],
            'mac_address': '00-14-22-01-23-45',
            'network_id': '18',
            'port_security_enabled': True,
            'qos_policy_id': '21',
            'revision_number': 22,
            'security_groups': ['23'],
            'status': '25',
            'tenant_id': '26',
            'updated_at': '2016-07-09T12:14:57.233772',

        })

        new_config = {
            'name': 'test_port_updated',
            'description': 'test_port_description_updated',
            'dns_domain': '123',
            'admin_state_up': False,
        }

        new_port = openstack.network.v2.port.Port(**{
            'id': '1',
            'name': 'test_port_updated',
            'description': 'test_port_description_updated',
            'admin_state_up': False,
            'binding_host_id': '3',
            'binding_profile': {'4': 4},
            'binding_vif_details': {'5': 5},
            'binding_vif_type': '6',
            'binding_vnic_type': '7',
            'created_at': '2016-03-09T12:14:57.233772',
            'data_plane_status': '32',
            'device_id': '9',
            'device_owner': '10',
            'dns_assignment': [{'11': 11}],
            'dns_domain': '123',
            'dns_name': '12',
            'extra_dhcp_opts': [{'13': 13}],
            'fixed_ips': [{'10.0.0.1': '10.0.0.2'}],
            'allowed_address_pairs': ['10.0.0.3', '10.0.0.4'],
            'mac_address': '00-14-22-01-23-45',
            'network_id': '18',
            'port_security_enabled': True,
            'qos_policy_id': '21',
            'revision_number': 22,
            'security_groups': ['23'],
            'status': '25',
            'tenant_id': '26',
            'updated_at': '2016-07-09T12:14:57.233772',

        })

        self.port_instance.resource_id = '1'
        self.fake_client.get_port = mock.MagicMock(return_value=old_port)
        self.fake_client.update_port = \
            mock.MagicMock(return_value=new_port)

        response = self.port_instance.update(new_config=new_config)
        self.assertNotEqual(response.name, old_port.name)
        self.assertNotEqual(response.description, old_port.description)
        self.assertNotEqual(response.dns_domain, old_port.dns_domain)
        self.assertNotEqual(response.is_admin_state_up,
                            old_port.is_admin_state_up)

    def test_delete_port(self):
        port = openstack.network.v2.port.Port(**{
            'id': '1',
            'name': 'test_port',
            'description': 'test_port_description',
            'admin_state_up': True,
            'binding_host_id': '3',
            'binding_profile': {'4': 4},
            'binding_vif_details': {'5': 5},
            'binding_vif_type': '6',
            'binding_vnic_type': '7',
            'created_at': '2016-03-09T12:14:57.233772',
            'data_plane_status': '32',
            'device_id': '9',
            'device_owner': '10',
            'dns_assignment': [{'11': 11}],
            'dns_domain': 'a11',
            'dns_name': '12',
            'extra_dhcp_opts': [{'13': 13}],
            'fixed_ips': [{'10.0.0.1': '10.0.0.2'}],
            'allowed_address_pairs': ['10.0.0.3', '10.0.0.4'],
            'mac_address': '00-14-22-01-23-45',
            'network_id': '18',
            'port_security_enabled': True,
            'qos_policy_id': '21',
            'revision_number': 22,
            'security_groups': ['23'],
            'status': '25',
            'tenant_id': '26',
            'updated_at': '2016-07-09T12:14:57.233772',

        })

        self.port_instance.resource_id = '1'
        self.fake_client.get_port = mock.MagicMock(return_value=port)
        self.fake_client.delete_port = mock.MagicMock(return_value=None)

        response = self.port_instance.delete()
        self.assertIsNone(response)
