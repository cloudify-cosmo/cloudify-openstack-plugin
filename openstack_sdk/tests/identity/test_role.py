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
import openstack.identity.v3.role

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import identity


class RoleTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(RoleTestCase, self).setUp()
        self.fake_client = self.generate_fake_openstack_connection('role')
        self.role_instance = identity.OpenstackRole(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.role_instance.connection = self.connection

    def test_get_role(self):
        role = openstack.identity.v3.role.Role(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_role',
            'description': 'old_description',
            'domain_id': 'test_domain_id',

        })
        self.role_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_role = mock.MagicMock(return_value=role)

        response = self.role_instance.get()
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.name, 'test_role')

    def test_list_roles(self):
        roles = [
            openstack.identity.v3.role.Role(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_role_1',
                'description': 'old_description',
                'domain_id': 'test_updated_domain_id',
            }),
            openstack.identity.v3.role.Role(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': 'test_role_2',
                'description': 'old_description',
                'email': 'test_updated_domain_id',
            }),
        ]

        self.fake_client.roles = mock.MagicMock(return_value=roles)

        response = self.role_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_role(self):
        role = {
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_role_1',
            'description': 'old_description',
            'domain_id': 'test_updated_domain_id',
        }

        new_res = openstack.identity.v3.role.Role(**role)
        self.role_instance.config = role
        self.fake_client.create_role = mock.MagicMock(return_value=new_res)

        response = self.role_instance.create()
        self.assertEqual(response.name, role['name'])

    def test_update_role(self):
        old_role = openstack.identity.v3.role.Role(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_role_1',
            'description': 'old_description',
            'domain_id': 'test_updated_domain_id',

        })

        new_config = {
            'name': 'test_updated_name',
            'description': 'new_description',
        }

        new_role = openstack.identity.v3.role.Role(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_updated_name',
            'description': 'new_description',
            'domain_id': 'test_updated_domain_id',

        })

        self.role_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_role = mock.MagicMock(return_value=old_role)
        self.fake_client.update_role = mock.MagicMock(return_value=new_role)

        response = self.role_instance.update(new_config=new_config)
        self.assertNotEqual(response.name, old_role.name)
        self.assertNotEqual(response.description, old_role.description)

    def test_delete_role(self):
        role = openstack.identity.v3.role.Role(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_role',
            'description': 'old_description',
            'domain_id': 'test_domain_id',

        })

        self.role_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_role = mock.MagicMock(return_value=role)
        self.fake_client.delete_role = mock.MagicMock(return_value=None)

        response = self.role_instance.delete()
        self.assertIsNone(response)
