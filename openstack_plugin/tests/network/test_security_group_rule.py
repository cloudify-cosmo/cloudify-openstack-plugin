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
import openstack.network.v2.security_group_rule

# Local imports
from openstack_plugin.tests.base import OpenStackTestBase
from openstack_plugin.resources.network import security_group_rule
from openstack_plugin.constants import (RESOURCE_ID,
                                        OPENSTACK_NAME_PROPERTY,
                                        OPENSTACK_TYPE_PROPERTY,
                                        SECURITY_GROUP_RULE_OPENSTACK_TYPE)


@mock.patch('openstack.connect')
class SecurityGroupRuleTestCase(OpenStackTestBase):

    def setUp(self):
        super(SecurityGroupRuleTestCase, self).setUp()

    @property
    def resource_config(self):
        return {
            'description': 'security_group_rule_description',
        }

    def test_create(self, mock_connection):
        # Prepare the context for create operation
        self._prepare_context_for_operation(
            test_name='SecurityGroupRuleTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.create')

        security_group_rule_instance = \
            openstack.network.v2.security_group_rule.SecurityGroupRule(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'created_at': '0',
                'description': '1',
                'direction': 'ingress',
                'ethertype': '3',
                'port_range_max': '80',
                'port_range_min': '80',
                'protocol': 'tcp',
                'remote_group_id': '7',
                'remote_ip_prefix': '0.0.0.0/0',
                'revision_number': 9,
                'security_group_id': 'a95b5509-c122-4c2f-823e-884bb559afe3',
                'tenant_id': '11',
                'updated_at': '12'
            })
        # Mock create security group rule response
        mock_connection().network.create_security_group_rule = \
            mock.MagicMock(return_value=security_group_rule_instance)

        # Call create security group rule
        security_group_rule.create()

        self.assertEqual(self._ctx.instance.runtime_properties[RESOURCE_ID],
                         'a95b5509-c122-4c2f-823e-884bb559afe8')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY],
            None)

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY],
            SECURITY_GROUP_RULE_OPENSTACK_TYPE)

    def test_delete(self, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            test_name='SecurityGroupRuleTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.delete')

        security_group_rule_instance = \
            openstack.network.v2.security_group_rule.SecurityGroupRule(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'created_at': '0',
                'description': '1',
                'direction': 'ingress',
                'ethertype': '3',
                'port_range_max': '80',
                'port_range_min': '80',
                'protocol': 'tcp',
                'remote_group_id': '7',
                'remote_ip_prefix': '0.0.0.0/0',
                'revision_number': 9,
                'security_group_id': 'a95b5509-c122-4c2f-823e-884bb559afe3',
                'tenant_id': '11',
                'updated_at': '12'
            })
        # Mock delete security group rule response
        mock_connection().network.delete_security_group_rule = \
            mock.MagicMock(return_value=None)

        # Mock get security group rule response
        mock_connection().network.get_security_group = \
            mock.MagicMock(return_value=security_group_rule_instance)

        # Call delete security group rule
        security_group_rule.delete()

        for attr in [RESOURCE_ID,
                     OPENSTACK_NAME_PROPERTY,
                     OPENSTACK_TYPE_PROPERTY]:
            self.assertNotIn(attr, self._ctx.instance.runtime_properties)

    def test_list_security_group_rules(self, mock_connection):
        # Prepare the context for list security group rules operation
        self._prepare_context_for_operation(
            test_name='SecurityGroupRuleTestCase',
            ctx_operation_name='cloudify.interfaces.operations.list')

        security_group_rules = [
            openstack.network.v2.security_group_rule.SecurityGroupRule(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe3',
                'created_at': '0',
                'description': '1',
                'direction': 'ingress',
                'ethertype': '3',
                'port_range_max': '80',
                'port_range_min': '80',
                'protocol': 'tcp',
                'remote_group_id': '7',
                'remote_ip_prefix': '0.0.0.0/0',
                'revision_number': 9,
                'security_group_id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'tenant_id': '11',
                'updated_at': '12'
            }),
            openstack.network.v2.security_group_rule.SecurityGroupRule(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe2',
                'created_at': '0',
                'description': '1',
                'direction': 'egress',
                'ethertype': '3',
                'port_range_max': '80',
                'port_range_min': '80',
                'protocol': 'tcp',
                'remote_group_id': '7',
                'remote_ip_prefix': '0.0.0.0/0',
                'revision_number': 9,
                'security_group_id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'tenant_id': '11',
                'updated_at': '12'
            })
        ]

        # Mock list security group rules response
        mock_connection().network.security_group_rules = \
            mock.MagicMock(return_value=security_group_rules)

        # Call list security group rules
        security_group_rule.list_security_group_rules()

        # Check if the security group rules list saved as runtime properties
        self.assertIn(
            'security_group_rule_list',
            self._ctx.instance.runtime_properties)

        # Check the size of security groups list
        self.assertEqual(
            len(self._ctx.instance.runtime_properties[
                    'security_group_rule_list']), 2)

    @mock.patch('openstack_sdk.common.OpenstackResource.get_quota_sets')
    def test_creation_validation(self, mock_quota_sets, mock_connection):
        # Prepare the context for creation validation operation
        self._prepare_context_for_operation(
            test_name='SecurityGroupRuleTestCase',
            ctx_operation_name='cloudify.interfaces.validation.creation')

        security_group_rules = [
            openstack.network.v2.security_group_rule.SecurityGroupRule(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe3',
                'created_at': '0',
                'description': '1',
                'direction': 'ingress',
                'ethertype': '3',
                'port_range_max': '80',
                'port_range_min': '80',
                'protocol': 'tcp',
                'remote_group_id': '7',
                'remote_ip_prefix': '0.0.0.0/0',
                'revision_number': 9,
                'security_group_id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'tenant_id': '11',
                'updated_at': '12'
            }),
            openstack.network.v2.security_group_rule.SecurityGroupRule(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe2',
                'created_at': '0',
                'description': '1',
                'direction': 'egress',
                'ethertype': '3',
                'port_range_max': '80',
                'port_range_min': '80',
                'protocol': 'tcp',
                'remote_group_id': '7',
                'remote_ip_prefix': '0.0.0.0/0',
                'revision_number': 9,
                'security_group_id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'tenant_id': '11',
                'updated_at': '12'
            })
        ]

        # Mock list security group rules response
        mock_connection().network.security_group_rules = \
            mock.MagicMock(return_value=security_group_rules)

        # Call list security group rules
        security_group_rule.list_security_group_rules()

        # Mock the quota size response
        mock_quota_sets.return_value = 20

        # Call creation validation
        security_group_rule.creation_validation()
