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
import openstack.network.v2.subnet

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import networks


class SubnetTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(SubnetTestCase, self).setUp()
        self.fake_client = self.generate_fake_openstack_connection('subnet')

        self.subnet_instance = networks.OpenstackSubnet(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.subnet_instance.connection = self.connection

    def test_get_subnet(self):
        subnet = openstack.network.v2.subnet.Subnet(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_name',
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
        self.subnet_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_subnet = mock.MagicMock(return_value=subnet)
        response = self.subnet_instance.get()
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.name, 'test_name')

    def test_list_subnets(self):
        subnets = [
            openstack.network.v2.subnet.Subnet(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_name_1',
                'description': 'test_description_1',
                'allocation_pools': [{'1': 1}],
                'cidr': '2',
                'created_at': '3',
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
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': 'test_name_2',
                'description': 'test_description_2',
                'allocation_pools': [{'1': 1}],
                'cidr': '2',
                'created_at': '3',
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
        ]

        self.fake_client.subnets = mock.MagicMock(return_value=subnets)
        response = self.subnet_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_subnet(self):
        subnet = {
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_name',
                'description': 'test_description',
                'allocation_pools': [{'1': 1}],
                'cidr': '2',
                'dns_nameservers': ['5'],
                'enable_dhcp': True,
                'gateway_ip': '6',
                'host_routes': ['7'],
                'ip_version': 8,
                'ipv6_address_mode': '9',
                'ipv6_ra_mode': '10',
                'network_id': '12',
                'segment_id': '14',
                'service_types': ['15'],
                'subnetpool_id': '16',
                'tenant_id': '17',
                'use_default_subnetpool': True,
        }

        new_res = openstack.network.v2.subnet.Subnet(**subnet)
        self.subnet_instance.config = subnet
        self.fake_client.create_subnet = mock.MagicMock(return_value=new_res)

        response = self.subnet_instance.create()
        self.assertEqual(response.name, subnet['name'])

    def test_update_subnet(self):
        old_subnet =\
            openstack.network.v2.subnet.Subnet(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_name',
                'description': 'test_description',
                'allocation_pools': [{'1': 1}],
                'cidr': '2',
                'created_at': '3',
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
            'name': 'test_name_update',
            'description': 'test_description_update',
            'enable_dhcp': False
        }

        new_subnet =\
            openstack.network.v2.subnet.Subnet(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_name_update',
                'description': 'test_description_update',
                'allocation_pools': [{'1': 1}],
                'cidr': '2',
                'created_at': '3',
                'dns_nameservers': ['5'],
                'enable_dhcp': False,
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

        self.subnet_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_subnet = mock.MagicMock(return_value=old_subnet)
        self.fake_client.update_subnet =\
            mock.MagicMock(return_value=new_subnet)

        response = self.subnet_instance.update(new_config=new_config)
        self.assertNotEqual(response.name, old_subnet.name)
        self.assertNotEqual(response.description, old_subnet.description)
        self.assertNotEqual(response.is_dhcp_enabled,
                            old_subnet.is_dhcp_enabled)

    def test_delete_subnet(self):
        subnet = openstack.network.v2.subnet.Subnet(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_name',
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

        self.subnet_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_subnet = mock.MagicMock(return_value=subnet)
        self.fake_client.delete_subnet = mock.MagicMock(return_value=None)
        response = self.subnet_instance.delete()
        self.assertIsNone(response)
