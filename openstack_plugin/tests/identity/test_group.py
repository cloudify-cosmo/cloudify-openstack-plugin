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
import openstack.identity.v3.group

# Local imports
from openstack_plugin.tests.base import OpenStackTestBase
from openstack_plugin.resources.identity import group
from openstack_plugin.constants import (RESOURCE_ID,
                                        OPENSTACK_NAME_PROPERTY,
                                        OPENSTACK_TYPE_PROPERTY,
                                        GROUP_OPENSTACK_TYPE)


@mock.patch('openstack.connect')
class GroupTestCase(OpenStackTestBase):

    def setUp(self):
        super(GroupTestCase, self).setUp()

    @property
    def resource_config(self):
        return {
            'name': 'test_group',
            'description': 'old_description',
            'domain_id': 'test_domain_id'
        }

    def test_create(self, mock_connection):
        # Prepare the context for create operation
        self._prepare_context_for_operation(
            test_name='GroupTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.create')

        group_instance = openstack.identity.v3.group.Group(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_group',
            'description': 'old_description',
            'domain_id': 'test_domain_id',

        })
        # Mock create group response
        mock_connection().identity.create_group = \
            mock.MagicMock(return_value=group_instance)

        # Call create group
        group.create(openstack_resource=None)

        self.assertEqual(self._ctx.instance.runtime_properties[RESOURCE_ID],
                         'a95b5509-c122-4c2f-823e-884bb559afe8')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY],
            'test_group')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY],
            GROUP_OPENSTACK_TYPE)

    def test_delete(self, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            test_name='GroupTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.delete')

        group_instance = openstack.identity.v3.group.Group(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_group',
            'description': 'old_description',
            'domain_id': 'test_domain_id',

        })
        # Mock delete group response
        mock_connection().identity.delete_group = \
            mock.MagicMock(return_value=group_instance)

        # Mock get group response
        mock_connection().identity.get_group = \
            mock.MagicMock(return_value=group_instance)

        # Call delete group
        group.delete(openstack_resource=None)

        for attr in [RESOURCE_ID,
                     OPENSTACK_NAME_PROPERTY,
                     OPENSTACK_TYPE_PROPERTY]:
            self.assertNotIn(attr, self._ctx.instance.runtime_properties)

    def test_update(self, mock_connection):
        # Prepare the context for update operation
        self._prepare_context_for_operation(
            test_name='GroupTestCase',
            ctx_operation_name='cloudify.interfaces.operations.update')

        old_group_instance = openstack.identity.v3.group.Group(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_group',
            'description': 'old_description',
            'domain_id': 'test_domain_id',

        })

        new_config = {
            'name': 'test_updated_group',
        }

        new_group_instance = openstack.identity.v3.group.Group(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_updated_group',
            'description': 'old_description',
            'domain_id': 'test_domain_id',

        })

        # Mock get group response
        mock_connection().identity.get_group = \
            mock.MagicMock(return_value=old_group_instance)

        # Mock update group response
        mock_connection().identity.update_group = \
            mock.MagicMock(return_value=new_group_instance)

        # Call update group
        group.update(args=new_config, openstack_resource=None)

    def test_list_groups(self, mock_connection):
        # Prepare the context for list groups operation
        self._prepare_context_for_operation(
            test_name='GroupTestCase',
            ctx_operation_name='cloudify.interfaces.operations.list')

        groups = [
            openstack.identity.v3.group.Group(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_group_!',
                'description': 'old_description',
                'domain_id': 'test_updated_domain_id',
            }),
            openstack.identity.v3.group.Group(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': 'test_group_2',
                'description': 'old_description',
                'domain_id': 'test_updated_domain_id',
            }),
        ]

        # Mock list groups response
        mock_connection().identity.groups = \
            mock.MagicMock(return_value=groups)

        # Mock find project response
        mock_connection().identity.find_project = \
            mock.MagicMock(return_value=self.project_resource)

        # Call list group
        group.list_groups(openstack_resource=None)

        # Check if the projects list saved as runtime properties
        self.assertIn(
            'group_list',
            self._ctx.instance.runtime_properties)

        # Check the size of project list
        self.assertEqual(
            len(self._ctx.instance.runtime_properties['group_list']), 2)
