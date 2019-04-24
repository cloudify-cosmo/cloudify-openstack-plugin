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
import openstack.identity.v2.user

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import identity


class UserTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(UserTestCase, self).setUp()
        self.fake_client = self.generate_fake_openstack_connection('user')
        self.user_instance = identity.OpenstackUser(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.user_instance.connection = self.connection

    def test_get_user(self):
        user = openstack.identity.v2.user.User(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_user',
            'is_enabled': True,
            'email': 'test_email@test.com',

        })
        self.user_instance.resource_id = 'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_user = mock.MagicMock(return_value=user)

        response = self.user_instance.get()
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.name, 'test_user')

    def test_list_users(self):
        users = [
            openstack.identity.v2.user.User(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_user_1',
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

        self.fake_client.users = mock.MagicMock(return_value=users)

        response = self.user_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_user(self):
        user = {
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_user_1',
            'is_enabled': True,
            'email': 'test1_email@test.com',
        }

        new_res = openstack.identity.v2.user.User(**user)
        self.user_instance.config = user
        self.fake_client.create_user = mock.MagicMock(return_value=new_res)

        response = self.user_instance.create()
        self.assertEqual(response.name, user['name'])

    def test_update_user(self):
        old_user = openstack.identity.v2.user.User(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_user_1',
            'is_enabled': True,
            'email': 'test1_email@test.com',

        })

        new_config = {
            'name': 'test_updated_name',
            'is_enabled': False,
        }

        new_user = openstack.identity.v2.user.User(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_updated_name',
            'is_enabled': False,
            'email': 'test1_email@test.com',

        })

        self.user_instance.resource_id = 'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_user = mock.MagicMock(return_value=old_user)
        self.fake_client.update_user = mock.MagicMock(return_value=new_user)

        response = self.user_instance.update(new_config=new_config)
        self.assertNotEqual(response.name, old_user.name)
        self.assertNotEqual(response.is_enabled, old_user.is_enabled)

    def test_delete_user(self):
        user = openstack.identity.v2.user.User(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_user',
            'is_enabled': True,
            'email': 'test_email@test.com',

        })

        self.user_instance.resource_id = 'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_user = mock.MagicMock(return_value=user)
        self.fake_client.delete_user = mock.MagicMock(return_value=None)

        response = self.user_instance.delete()
        self.assertIsNone(response)
