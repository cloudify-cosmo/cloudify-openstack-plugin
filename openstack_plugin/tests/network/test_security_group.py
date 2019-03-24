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
import openstack.network.v2.security_group
import openstack.network.v2.security_group_rule

# Local imports
from openstack_plugin.tests.base import OpenStackTestBase
from openstack_plugin.resources.network import security_group
from openstack_plugin.constants import (RESOURCE_ID,
                                        OPENSTACK_NAME_PROPERTY,
                                        OPENSTACK_TYPE_PROPERTY,
                                        SECURITY_GROUP_OPENSTACK_TYPE)


@mock.patch('openstack.connect')
class SecurityGroupTestCase(OpenStackTestBase):

    def setUp(self):
        super(SecurityGroupTestCase, self).setUp()

    @property
    def resource_config(self):
        return {
            'name': 'test_security_group',
            'description': 'security_group_description',
        }

    def test_create(self, mock_connection):
        # Prepare the context for create operation
        self._prepare_context_for_operation(
            test_name='SecurityGroupTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.create')

        security_group_instance = \
            openstack.network.v2.security_group.SecurityGroup(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_security_group',
                'created_at': '2016-10-04T12:14:57.233772',
                'description': '1',
                'revision_number': 3,
                'tenant_id': '4',
                'updated_at': '2016-10-14T12:16:57.233772',
                'tags': ['5']
            })
        # Mock create security group response
        mock_connection().network.create_security_group = \
            mock.MagicMock(return_value=security_group_instance)

        # Call create security group
        security_group.create()

        self.assertEqual(self._ctx.instance.runtime_properties[RESOURCE_ID],
                         'a95b5509-c122-4c2f-823e-884bb559afe8')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY],
            'test_security_group')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY],
            SECURITY_GROUP_OPENSTACK_TYPE)

    def test_configure(self, mock_connection):
        # Prepare the context for configure operation
        self._prepare_context_for_operation(
            test_name='SecurityGroupTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.configure',
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8'
            })

        security_group_rules = [
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
        # Mock get security group response
        mock_connection().network.create_security_group_rule = \
            mock.MagicMock(side_effect=security_group_rules)

        # Call configure in order to add security group rules
        security_group.configure(security_group_rules=[
            {
                'remote_ip_prefix': '0.0.0.0/0',
                'port_range_max': '80',
                'port_range_min': '80',
                'direction': 'ingress',
                'protocol': 'tcp'
            },
            {
                'remote_ip_prefix': '0.0.0.0/0',
                'port_range_max': '80',
                'port_range_min': '80',
                'direction': 'egress',
                'protocol': 'tcp'
            }
        ])

    def test_disable_default_egress_rules(self, mock_connection):
        # Prepare the context for configure operation
        properties = dict()
        properties['disable_default_egress_rules'] = True
        properties.update(self.node_properties)

        self._prepare_context_for_operation(
            test_name='SecurityGroupTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.configure',
            test_properties=properties,
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8'
            })

        default_security_group_rules = [
            openstack.network.v2.security_group_rule.SecurityGroupRule(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe2',
                'created_at': '0',
                'description': '1',
                'direction': 'ingress',
                'ethertype': 'IPv4',
                'port_range_max': '-1',
                'port_range_min': '-1',
                'protocol': 'tcp',
                'remote_group_id': '7',
                'remote_ip_prefix': '0.0.0.0/0',
                'revision_number': 9,
                'security_group_id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'tenant_id': '11',
                'updated_at': '12'
            }),
            openstack.network.v2.security_group_rule.SecurityGroupRule(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe4',
                'created_at': '0',
                'description': '1',
                'direction': 'ingress',
                'ethertype': 'IPv6',
                'port_range_max': '-1',
                'port_range_min': '-1',
                'protocol': 'tcp',
                'remote_group_id': '7',
                'remote_ip_prefix': '::/0',
                'revision_number': 9,
                'security_group_id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'tenant_id': '11',
                'updated_at': '12'
            })
        ]

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
        # Mock create security group rule response
        mock_connection().network.create_security_group_rule = \
            mock.MagicMock(side_effect=security_group_rules)

        # Mock delete security group rule response
        mock_connection().network.delete_security_group_rule = \
            mock.MagicMock(retrun_value=None)

        # Mock list security group rules response
        mock_connection().network.security_group_rules = \
            mock.MagicMock(retrun_value=default_security_group_rules)

        # Call configure in order to add security group rules
        security_group.configure(security_group_rules=[
            {
                'remote_ip_prefix': '0.0.0.0/0',
                'port_range_max': '80',
                'port_range_min': '80',
                'direction': 'ingress',
                'protocol': 'tcp'
            },
            {
                'remote_ip_prefix': '0.0.0.0/0',
                'port_range_max': '80',
                'port_range_min': '80',
                'direction': 'egress',
                'protocol': 'tcp'
            }
        ])

    def test_delete(self, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            test_name='SecurityGroupTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.delete')

        security_group_instance = \
            openstack.network.v2.security_group.SecurityGroup(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_security_group',
                'created_at': '2016-10-04T12:14:57.233772',
                'description': '1',
                'revision_number': 3,
                'tenant_id': '4',
                'updated_at': '2016-10-14T12:16:57.233772',
                'tags': ['5']
            })
        # Mock delete security group response
        mock_connection().network.delete_security_group = \
            mock.MagicMock(return_value=None)

        # Mock get security group response
        mock_connection().network.get_security_group = \
            mock.MagicMock(return_value=security_group_instance)

        # Call delete security group
        security_group.delete()

        for attr in [RESOURCE_ID,
                     OPENSTACK_NAME_PROPERTY,
                     OPENSTACK_TYPE_PROPERTY]:
            self.assertNotIn(attr, self._ctx.instance.runtime_properties)

    def test_update(self, mock_connection):
        # Prepare the context for update operation
        self._prepare_context_for_operation(
            test_name='SecurityGroupTestCase',
            ctx_operation_name='cloudify.interfaces.operations.update')

        old_security_group_instance = \
            openstack.network.v2.security_group.SecurityGroup(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_security_group',
                'created_at': '2016-10-04T12:14:57.233772',
                'description': '1',
                'revision_number': 3,
                'tenant_id': '4',
                'updated_at': '2016-10-14T12:16:57.233772',
                'tags': ['5']
            })

        new_config = {
            'name': 'test_updated_security_group',
        }

        new_security_group_instance = \
            openstack.network.v2.security_group.SecurityGroup(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_updated_security_group',
                'created_at': '2016-10-04T12:14:57.233772',
                'description': '1',
                'revision_number': 3,
                'tenant_id': '4',
                'updated_at': '2016-10-14T12:16:57.233772',
                'tags': ['5']
            })

        # Mock get security group response
        mock_connection().network.get_security_group = \
            mock.MagicMock(return_value=old_security_group_instance)

        # Mock update security group response
        mock_connection().network.update_security_group = \
            mock.MagicMock(return_value=new_security_group_instance)

        # Call update security group
        security_group.update(args=new_config)

    def test_list_security_groups(self, mock_connection):
        # Prepare the context for list security groups operation
        self._prepare_context_for_operation(
            test_name='SecurityGroupTestCase',
            ctx_operation_name='cloudify.interfaces.operations.list')

        security_groups = [
            openstack.network.v2.security_group.SecurityGroup(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_security_group_1',
                'created_at': '2016-10-04T12:14:57.233772',
                'description': '1',
                'revision_number': 3,
                'tenant_id': '4',
                'updated_at': '2016-10-14T12:16:57.233772',
                'tags': ['5']
            }),
            openstack.network.v2.security_group.SecurityGroup(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe3',
                'name': 'test_security_group_2',
                'created_at': '2016-10-04T12:14:57.233772',
                'description': '1',
                'revision_number': 3,
                'tenant_id': '4',
                'updated_at': '2016-10-14T12:16:57.233772',
                'tags': ['5']
            }),
        ]

        # Mock list security groups response
        mock_connection().network.security_groups = \
            mock.MagicMock(return_value=security_groups)

        # Call list security groups
        security_group.list_security_groups()

        # Check if the security groups list saved as runtime properties
        self.assertIn(
            'security_group_list',
            self._ctx.instance.runtime_properties)

        # Check the size of security groups list
        self.assertEqual(
            len(self._ctx.instance.runtime_properties['security_group_list']),
            2)

    @mock.patch('openstack_sdk.common.OpenstackResource.get_quota_sets')
    def test_creation_validation(self, mock_quota_sets, mock_connection):
        # Prepare the context for creation validation operation
        self._prepare_context_for_operation(
            test_name='SecurityGroupTestCase',
            ctx_operation_name='cloudify.interfaces.validation.creation')

        security_groups = [
            openstack.network.v2.security_group.SecurityGroup(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_security_group_1',
                'created_at': '2016-10-04T12:14:57.233772',
                'description': '1',
                'revision_number': 3,
                'tenant_id': '4',
                'updated_at': '2016-10-14T12:16:57.233772',
                'tags': ['5']
            }),
            openstack.network.v2.security_group.SecurityGroup(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe3',
                'name': 'test_security_group_2',
                'created_at': '2016-10-04T12:14:57.233772',
                'description': '1',
                'revision_number': 3,
                'tenant_id': '4',
                'updated_at': '2016-10-14T12:16:57.233772',
                'tags': ['5']
            }),
        ]

        # Mock list security groups response
        mock_connection().network.routers = \
            mock.MagicMock(return_value=security_groups)

        # Mock the quota size response
        mock_quota_sets.return_value = 20

        # Call creation validation
        security_group.creation_validation()
