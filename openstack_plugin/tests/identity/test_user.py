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
import openstack.identity.v2.user

# Local imports
from openstack_plugin.tests.base import OpenStackTestBase
from openstack_plugin.resources.identity import user
from openstack_plugin.constants import (RESOURCE_ID,
                                        OPENSTACK_NAME_PROPERTY,
                                        OPENSTACK_TYPE_PROPERTY,
                                        USER_OPENSTACK_TYPE)


@mock.patch('openstack.connect')
class UserTestCase(OpenStackTestBase):

    def setUp(self):
        super(UserTestCase, self).setUp()

    @property
    def resource_config(self):
        return {
            'name': 'test_user',
            'is_enabled': True,
            'email': 'test_email@test.com'
        }

    def test_create(self, mock_connection):
        # Prepare the context for create operation
        self._prepare_context_for_operation(
            test_name='UserTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.create')

        user_instance = openstack.identity.v2.user.User(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_user',
            'is_enabled': True,
            'email': 'test_email@test.com',

        })
        # Mock create user response
        mock_connection().identity.create_user = \
            mock.MagicMock(return_value=user_instance)

        # Call create user
        user.create(openstack_resource=None)

        self.assertEqual(self._ctx.instance.runtime_properties[RESOURCE_ID],
                         'a95b5509-c122-4c2f-823e-884bb559afe8')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY],
            'test_user')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY],
            USER_OPENSTACK_TYPE)

    def test_delete(self, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            test_name='UserTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.delete')

        user_instance = openstack.identity.v2.user.User(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_user',
            'is_enabled': True,
            'email': 'test_email@test.com',

        })
        # Mock delete user response
        mock_connection().identity.delete_user = \
            mock.MagicMock(return_value=user_instance)

        # Mock get user response
        mock_connection().identity.get_user = \
            mock.MagicMock(return_value=user_instance)

        # Call delete user
        user.delete(openstack_resource=None)

        for attr in [RESOURCE_ID,
                     OPENSTACK_NAME_PROPERTY,
                     OPENSTACK_TYPE_PROPERTY]:
            self.assertNotIn(attr, self._ctx.instance.runtime_properties)

    def test_update(self, mock_connection):
        # Prepare the context for update operation
        self._prepare_context_for_operation(
            test_name='UserTestCase',
            ctx_operation_name='cloudify.interfaces.operations.update')

        old_user_instance = openstack.identity.v2.user.User(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_user',
            'is_enabled': True,
            'email': 'test_email@test.com',

        })

        new_config = {
            'name': 'test_updated_user',
        }

        new_user_instance = openstack.identity.v2.user.User(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_updated_user',
            'is_enabled': True,
            'email': 'test_email@test.com',

        })

        # Mock get user response
        mock_connection().identity.get_user = \
            mock.MagicMock(return_value=old_user_instance)

        # Mock update user response
        mock_connection().identity.update_user = \
            mock.MagicMock(return_value=new_user_instance)

        # Call update user
        user.update(args=new_config, openstack_resource=None)

    def test_list_users(self,
                        mock_connection):
        # Prepare the context for list users operation
        self._prepare_context_for_operation(
            test_name='UserTestCase',
            ctx_operation_name='cloudify.interfaces.operations.list')

        users = [
            openstack.identity.v2.user.User(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_user_!',
                'is_enabled': True,
                'email': 'test1_email@test.com',
            }),
            openstack.identity.v2.user.User(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': 'test_user_2',
                'is_enabled': True,
                'email': 'test2_email@test.com',
            }),
        ]

        # Mock list users response
        mock_connection().identity.users = \
            mock.MagicMock(return_value=users)

        # Mock find project response
        mock_connection().identity.find_project = \
            mock.MagicMock(return_value=self.project_resource)

        # Call list user
        user.list_users(openstack_resource=None)

        # Check if the projects list saved as runtime properties
        self.assertIn(
            'user_list',
            self._ctx.instance.runtime_properties)

        # Check the size of project list
        self.assertEqual(
            len(self._ctx.instance.runtime_properties['user_list']), 2)
