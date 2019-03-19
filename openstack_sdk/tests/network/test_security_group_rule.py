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
import openstack.network.v2.security_group_rule

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import networks


class SecurityGroupRuleTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(SecurityGroupRuleTestCase, self).setUp()
        self.fake_client =\
            self.generate_fake_openstack_connection('security_group_rule')

        self.security_group_rule_instance =\
            networks.OpenstackSecurityGroupRule(
                client_config=self.client_config,
                logger=mock.MagicMock()
            )
        self.security_group_rule_instance.connection = self.connection

    def test_get_security_group_rule(self):
        sg_rule =\
            openstack.network.v2.security_group_rule.SecurityGroupRule(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_name',
                'created_at': '0',
                'description': '1',
                'direction': '2',
                'ethertype': '3',
                'port_range_max': 4,
                'port_range_min': 5,
                'protocol': '6',
                'remote_group_id': '7',
                'remote_ip_prefix': '8',
                'revision_number': 9,
                'security_group_id': '10',
                'tenant_id': '11',
                'updated_at': '12'
            })
        self.security_group_rule_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_security_group_rule =\
            mock.MagicMock(return_value=sg_rule)

        response = self.security_group_rule_instance.get()
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.name, 'test_name')

    def test_list_security_group_rules(self):
        sgs = [
            openstack.network.v2.security_group_rule.SecurityGroupRule(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_name_1',
                'created_at': '0',
                'description': '1',
                'direction': '2',
                'ethertype': '3',
                'port_range_max': 4,
                'port_range_min': 5,
                'protocol': '6',
                'remote_group_id': '7',
                'remote_ip_prefix': '8',
                'revision_number': 9,
                'security_group_id': '10',
                'tenant_id': '11',
                'updated_at': '12'
            }),
            openstack.network.v2.security_group_rule.SecurityGroupRule(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': 'test_name_2',
                'created_at': '0',
                'description': '1',
                'direction': '2',
                'ethertype': '3',
                'port_range_max': 4,
                'port_range_min': 5,
                'protocol': '6',
                'remote_group_id': '7',
                'remote_ip_prefix': '8',
                'revision_number': 9,
                'security_group_id': '10',
                'tenant_id': '11',
                'updated_at': '12'
            })
        ]

        self.fake_client.security_group_rules =\
            mock.MagicMock(return_value=sgs)
        response = self.security_group_rule_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_security_group_rule(self):
        rule = {
                'id:': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_name',
                'description': 'test_description',
                'availability_zone_hints': ['1'],
                'availability_zones': ['2'],
                'distributed': False,
                'flavor_id': '5',
                'ha': False,
                'routes': ['8'],
                'tenant_id': '10',
        }

        new_res =\
            openstack.network.v2.security_group_rule.SecurityGroupRule(**rule)
        self.security_group_rule_instance.config = rule
        self.fake_client.create_security_group_rule =\
            mock.MagicMock(return_value=new_res)

        response = self.security_group_rule_instance.create()
        self.assertEqual(response.name, rule['name'])
        self.assertEqual(response.description, rule['description'])

    def test_delete_security_group_rule(self):
        sg = openstack.network.v2.security_group_rule.SecurityGroupRule(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_name',
            'description': 'test_description',
            'created_at': '0',
            'direction': '2',
            'ethertype': '3',
            'port_range_max': 4,
            'port_range_min': 5,
            'protocol': '6',
            'remote_group_id': '7',
            'remote_ip_prefix': '8',
            'revision_number': 9,
            'security_group_id': '10',
            'tenant_id': '11',
            'updated_at': '12'

        })

        self.security_group_rule_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_security_group_rule =\
            mock.MagicMock(return_value=sg)
        self.fake_client.delete_security_group_rule = \
            mock.MagicMock(return_value=None)

        response = self.security_group_rule_instance.delete()
        self.assertIsNone(response)
