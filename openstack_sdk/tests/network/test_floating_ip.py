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
import openstack.network.v2.floating_ip

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import networks


class FloatingIPTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(FloatingIPTestCase, self).setUp()

        self.fake_client =\
            self.generate_fake_openstack_connection('floating_ip')

        self.floating_ip_instance = networks.OpenstackFloatingIP(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.floating_ip_instance.connection = self.connection

    def test_get_floating_ip(self):
        floating_ip = openstack.network.v2.floating_ip.FloatingIP(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'description': 'test_description',
            'name': '127.0.0.1',
            'created_at': '0',
            'fixed_ip_address': '1',
            'floating_ip_address': '127.0.0.1',
            'floating_network_id': '3',
            'port_id': '5',
            'qos_policy_id': '51',
            'tenant_id': '6',
            'router_id': '7',
            'dns_domain': '9',
            'dns_name': '10',
            'status': 'ACTIVE',
            'revision_number': 12,
            'updated_at': '13',
            'subnet_id': '14',
            'tags': ['15', '16']

        })
        self.floating_ip_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_ip = mock.MagicMock(return_value=floating_ip)

        response = self.floating_ip_instance.get()
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.name, '127.0.0.1')
        self.assertEqual(response.description, 'test_description')

    @mock.patch('openstack_sdk.common.'
                'OpenstackResource.get_project_id_by_name')
    def test_list_floating_ips(self, mock_project):
        mock_project.return_value = '1b6s22a21fdf512d973b325ddd843306'
        ips = [
            openstack.network.v2.floating_ip.FloatingIP(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'description': 'test_description_1',
                'name': 'test_name_1',
                'created_at': '0',
                'fixed_ip_address': '1',
                'floating_ip_address': '127.0.0.1',
                'floating_network_id': '3',
                'port_id': '5',
                'qos_policy_id': '51',
                'tenant_id': '6',
                'router_id': '7',
                'dns_domain': '9',
                'dns_name': '10',
                'status': 'ACTIVE',
                'revision_number': 12,
                'updated_at': '13',
                'subnet_id': '14',
                'tags': ['15', '16']

            }),
            openstack.network.v2.floating_ip.FloatingIP(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'description': 'test_description_2',
                'name': 'test_name_2',
                'created_at': '0',
                'fixed_ip_address': '1',
                'floating_ip_address': '127.0.0.1',
                'floating_network_id': '3',
                'port_id': '5',
                'qos_policy_id': '51',
                'tenant_id': '6',
                'router_id': '7',
                'dns_domain': '9',
                'dns_name': '10',
                'status': 'ACTIVE',
                'revision_number': 12,
                'updated_at': '13',
                'subnet_id': '14',
                'tags': ['15', '16']

            })
        ]

        self.fake_client.ips = mock.MagicMock(return_value=ips)

        response = self.floating_ip_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_floating_ip(self):
        floating_ip = {
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'description': 'test_description',
            'name': '127.0.0.1',
            'fixed_ip_address': '1',
            'floating_ip_address': '127.0.0.1',
            'floating_network_id': '3',
            'port_id': '5',
            'tenant_id': '6',
            'router_id': '7',
            'dns_domain': '9',
            'dns_name': '10',
            'subnet_id': '14',
            'tags': ['15', '16']
        }

        new_res = openstack.network.v2.floating_ip.FloatingIP(**floating_ip)
        self.floating_ip_instance.config = floating_ip
        self.fake_client.create_ip = mock.MagicMock(return_value=new_res)

        response = self.floating_ip_instance.create()
        self.assertEqual(response.name, floating_ip['name'])
        self.assertEqual(response.description, floating_ip['description'])

    def test_update_floating_ip(self):
        old_ip = openstack.network.v2.floating_ip.FloatingIP(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'description': 'test_description',
            'name': 'test_name_1',
            'created_at': '0',
            'fixed_ip_address': '1',
            'floating_ip_address': '127.0.0.1',
            'floating_network_id': '3',
            'port_id': '5',
            'qos_policy_id': '51',
            'tenant_id': '6',
            'router_id': '7',
            'dns_domain': '9',
            'dns_name': '10',
            'status': 'ACTIVE',
            'revision_number': 12,
            'updated_at': '13',
            'subnet_id': '14',
            'tags': ['15', '16']

        })

        new_config = {
            'port_id': '7',
            'fixed_ip_address': '2',
            'description': 'test_description_update',
        }

        new_ip = openstack.network.v2.floating_ip.FloatingIP(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'description': 'test_description_update',
            'name': 'test_name',
            'created_at': '0',
            'fixed_ip_address': '2',
            'floating_ip_address': '127.0.0.1',
            'floating_network_id': '3',
            'port_id': '7',
            'qos_policy_id': '51',
            'tenant_id': '6',
            'router_id': '7',
            'dns_domain': '9',
            'dns_name': '10',
            'status': 'ACTIVE',
            'revision_number': 12,
            'updated_at': '13',
            'subnet_id': '14',
            'tags': ['15', '16']

        })

        self.floating_ip_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_ip = mock.MagicMock(return_value=old_ip)
        self.fake_client.update_ip = mock.MagicMock(return_value=new_ip)

        response = self.floating_ip_instance.update(new_config=new_config)
        self.assertNotEqual(response.description, old_ip.description)
        self.assertNotEqual(response.fixed_ip_address, old_ip.fixed_ip_address)
        self.assertNotEqual(response.port_id, old_ip.port_id)

    def test_delete_floating_ip(self):
        floating_ip = openstack.network.v2.floating_ip.FloatingIP(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'description': 'test_description',
            'name': 'test_name',
            'created_at': '0',
            'fixed_ip_address': '1',
            'floating_ip_address': '127.0.0.1',
            'floating_network_id': '3',
            'port_id': '5',
            'qos_policy_id': '51',
            'tenant_id': '6',
            'router_id': '7',
            'dns_domain': '9',
            'dns_name': '10',
            'status': 'ACTIVE',
            'revision_number': 12,
            'updated_at': '13',
            'subnet_id': '14',
            'tags': ['15', '16']

        })

        self.floating_ip_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_ip = mock.MagicMock(return_value=floating_ip)
        self.fake_client.delete_ip = mock.MagicMock(return_value=None)

        response = self.floating_ip_instance.delete()
        self.assertIsNone(response)
