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
import openstack.compute.v2.server_group
from cloudify.exceptions import NonRecoverableError

# Local imports
from openstack_plugin.tests.base import OpenStackTestBase
from openstack_plugin.resources.compute import server_group
from openstack_plugin.constants import (RESOURCE_ID,
                                        OPENSTACK_NAME_PROPERTY,
                                        OPENSTACK_TYPE_PROPERTY,
                                        SERVER_GROUP_OPENSTACK_TYPE)


@mock.patch('openstack.connect')
class ServerGroupTestCase(OpenStackTestBase):

    def setUp(self):
        super(ServerGroupTestCase, self).setUp()

    @property
    def resource_config(self):
        return {
            'name': 'test_server_group',
            'description': 'server_group_description'
        }

    def test_create(self, mock_connection):
        # Prepare the context for create operation
        self._prepare_context_for_operation(
            test_name='ServerGroupTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.create')

        server_instance = openstack.compute.v2.server_group.ServerGroup(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server_group',
            'members': ['server1', 'server2'],
            'metadata': {'k': 'v'},
            'policies': ['anti-affinity'],

        })
        # Mock create server group response
        mock_connection().compute.create_server_group = \
            mock.MagicMock(return_value=server_instance)

        # Call create server group
        server_group.create()

        self.assertEqual(self._ctx.instance.runtime_properties[RESOURCE_ID],
                         'a95b5509-c122-4c2f-823e-884bb559afe8')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY],
            'test_server_group')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY],
            SERVER_GROUP_OPENSTACK_TYPE)

    def test_delete(self, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            test_name='ServerGroupTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.delete')

        server_instance = openstack.compute.v2.server_group.ServerGroup(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server_group',
            'members': ['server1', 'server2'],
            'metadata': {'k': 'v'},
            'policies': ['anti-affinity'],

        })
        # Mock delete server group response
        mock_connection().compute.delete_server_group = \
            mock.MagicMock(return_value=None)

        # Mock delete server group response
        mock_connection().compute.get_server_group = \
            mock.MagicMock(return_value=server_instance)

        # Call delete server group
        server_group.delete()

        for attr in [RESOURCE_ID,
                     OPENSTACK_NAME_PROPERTY,
                     OPENSTACK_TYPE_PROPERTY]:
            self.assertNotIn(attr,
                             self._ctx.instance.runtime_properties)

    def test_update(self, _):
        # Prepare the context for update operation
        self._prepare_context_for_operation(
            test_name='ServerGroupTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.update')

        updated_config = {
            'name': 'Updated Name'
        }

        with self.assertRaises(NonRecoverableError):
            # Call update server group
            server_group.update(args=updated_config)

    def test_list_server_groups(self, mock_connection):
        # Prepare the context for list server groups operation
        self._prepare_context_for_operation(
            test_name='ServerGroupTestCase',
            ctx_operation_name='cloudify.interfaces.operations.list')

        server_group_list = [
            openstack.compute.v2.server_group.ServerGroup(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_server_group_1',
                'members': ['server1', 'server2'],
                'metadata': {'k': 'v'},
                'policies': ['anti-affinity'],
            }),
            openstack.compute.v2.server_group.ServerGroup(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': 'test_server_group_2',
                'members': ['server2', 'server3'],
                'metadata': {'k': 'v'},
                'policies': ['anti-affinity'],
            }),
        ]
        # Mock list keypairs
        mock_connection().compute.server_groups = \
            mock.MagicMock(return_value=server_group_list)

        # Call list server groups
        server_group.list_server_groups()

        # Check if the server groups list saved as runtime properties
        self.assertIn(
            'server_group_list',
            self._ctx.instance.runtime_properties)

        # Check the size of server groups list
        self.assertEqual(
            len(self._ctx.instance.runtime_properties['server_group_list']), 2)

    @mock.patch('openstack_sdk.common.OpenstackResource.get_quota_sets')
    def test_creation_validation(self, mock_quota_sets, mock_connection):
        # Prepare the context for creation validation server groups operation
        self._prepare_context_for_operation(
            test_name='ServerGroupTestCase',
            ctx_operation_name='cloudify.interfaces.validation.creation')

        server_group_list = [
            openstack.compute.v2.server_group.ServerGroup(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_server_group_1',
                'members': ['server1', 'server2'],
                'metadata': {'k': 'v'},
                'policies': ['anti-affinity'],
            }),
            openstack.compute.v2.server_group.ServerGroup(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': 'test_server_group_2',
                'members': ['server2', 'server3'],
                'metadata': {'k': 'v'},
                'policies': ['anti-affinity'],
            }),
        ]
        # Mock list server groups
        mock_connection().compute.server_groups = \
            mock.MagicMock(return_value=server_group_list)

        # Mock the quota size response
        mock_quota_sets.return_value = 20

        # Call creation validation
        server_group.creation_validation()
