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
import openstack.identity.v3.role

# Local imports
from openstack_plugin.tests.base import OpenStackTestBase
from openstack_plugin.resources.identity import role
from openstack_plugin.constants import (RESOURCE_ID,
                                        OPENSTACK_NAME_PROPERTY,
                                        OPENSTACK_TYPE_PROPERTY,
                                        ROLE_OPENSTACK_TYPE)


@mock.patch('openstack.connect')
class RoleTestCase(OpenStackTestBase):

    def setUp(self):
        super(RoleTestCase, self).setUp()

    @property
    def resource_config(self):
        return {
            'name': 'test_role',
            'description': 'old_description',
            'domain_id': 'test_domain_id'
        }

    def test_create(self, mock_connection):
        # Prepare the context for create operation
        self._prepare_context_for_operation(
            test_name='RoleTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.create')

        role_instance = openstack.identity.v3.role.Role(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_role',
            'description': 'old_description',
            'domain_id': 'test_domain_id',

        })
        # Mock create role response
        mock_connection().identity.create_role = \
            mock.MagicMock(return_value=role_instance)

        # Call create role
        role.create()

        self.assertEqual(self._ctx.instance.runtime_properties[RESOURCE_ID],
                         'a95b5509-c122-4c2f-823e-884bb559afe8')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY],
            'test_role')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY],
            ROLE_OPENSTACK_TYPE)

    def test_delete(self, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            test_name='RoleTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.delete')

        role_instance = openstack.identity.v3.role.Role(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_role',
            'description': 'old_description',
            'domain_id': 'test_domain_id',

        })
        # Mock delete role response
        mock_connection().identity.delete_role = \
            mock.MagicMock(return_value=role_instance)

        # Mock get role response
        mock_connection().identity.get_role = \
            mock.MagicMock(return_value=role_instance)

        # Call delete role
        role.delete()

        for attr in [RESOURCE_ID,
                     OPENSTACK_NAME_PROPERTY,
                     OPENSTACK_TYPE_PROPERTY]:
            self.assertNotIn(attr, self._ctx.instance.runtime_properties)

    def test_update(self, mock_connection):
        # Prepare the context for update operation
        self._prepare_context_for_operation(
            test_name='RoleTestCase',
            ctx_operation_name='cloudify.interfaces.operations.update')

        old_role_instance = openstack.identity.v3.role.Role(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_role',
            'description': 'old_description',
            'domain_id': 'test_domain_id',

        })

        new_config = {
            'name': 'test_updated_role',
        }

        new_role_instance = openstack.identity.v3.role.Role(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_updated_role',
            'description': 'old_description',
            'domain_id': 'test_domain_id',

        })

        # Mock get role response
        mock_connection().identity.get_role = \
            mock.MagicMock(return_value=old_role_instance)

        # Mock update role response
        mock_connection().identity.update_role = \
            mock.MagicMock(return_value=new_role_instance)

        # Call update role
        role.update(args=new_config)

    def test_list_roles(self, mock_connection):
        # Prepare the context for list roles operation
        self._prepare_context_for_operation(
            test_name='RoleTestCase',
            ctx_operation_name='cloudify.interfaces.operations.list')

        roles = [
            openstack.identity.v3.role.Role(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_role_!',
                'description': 'old_description',
                'domain_id': 'test_updated_domain_id',
            }),
            openstack.identity.v3.role.Role(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': 'test_role_2',
                'description': 'old_description',
                'domain_id': 'test_updated_domain_id',
            }),
        ]

        # Mock list roles response
        mock_connection().identity.roles = \
            mock.MagicMock(return_value=roles)

        # Mock find project response
        mock_connection().identity.find_project = \
            mock.MagicMock(return_value=self.project_resource)

        # Call list role
        role.list_roles()

        # Check if the projects list saved as runtime properties
        self.assertIn(
            'role_list',
            self._ctx.instance.runtime_properties)

        # Check the size of project list
        self.assertEqual(
            len(self._ctx.instance.runtime_properties['role_list']), 2)
