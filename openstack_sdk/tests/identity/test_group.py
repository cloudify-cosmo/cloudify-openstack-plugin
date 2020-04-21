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
import openstack.identity.v3.group

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import identity


class GroupTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(GroupTestCase, self).setUp()
        self.fake_client = self.generate_fake_openstack_connection('group')
        self.group_instance = identity.OpenstackGroup(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.group_instance.connection = self.connection

    def test_get_group(self):
        group = openstack.identity.v3.group.Group(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_group',
            'description': 'old_description',
            'domain_id': 'test_domain_id',

        })
        self.group_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_group = mock.MagicMock(return_value=group)

        response = self.group_instance.get()
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.name, 'test_group')

    def test_list_groups(self):
        groups = [
            openstack.identity.v3.group.Group(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_group_1',
                'description': 'old_description',
                'domain_id': 'test_updated_domain_id',
            }),
            openstack.identity.v3.group.Group(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': 'test_group_2',
                'description': 'old_description',
                'email': 'test_updated_domain_id',
            }),
        ]

        self.fake_client.groups = mock.MagicMock(return_value=groups)

        response = self.group_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_group(self):
        group = {
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_group_1',
            'description': 'old_description',
            'domain_id': 'test_updated_domain_id',
        }

        new_res = openstack.identity.v3.group.Group(**group)
        self.group_instance.config = group
        self.fake_client.create_group = mock.MagicMock(return_value=new_res)

        response = self.group_instance.create()
        self.assertEqual(response.name, group['name'])

    def test_update_group(self):
        old_group = openstack.identity.v3.group.Group(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_group_1',
            'description': 'old_description',
            'domain_id': 'test_updated_domain_id',

        })

        new_config = {
            'name': 'test_updated_name',
            'description': 'new_description',
        }

        new_group = openstack.identity.v3.group.Group(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_updated_name',
            'description': 'new_description',
            'domain_id': 'test_updated_domain_id',

        })

        self.group_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_group = mock.MagicMock(return_value=old_group)
        self.fake_client.update_group = mock.MagicMock(return_value=new_group)

        response = self.group_instance.update(new_config=new_config)
        self.assertNotEqual(response.name, old_group.name)
        self.assertNotEqual(response.description, old_group.description)

    def test_delete_group(self):
        group = openstack.identity.v3.group.Group(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_group',
            'description': 'old_description',
            'domain_id': 'test_domain_id',

        })

        self.group_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_group = mock.MagicMock(return_value=group)
        self.fake_client.delete_group = mock.MagicMock(return_value=None)

        response = self.group_instance.delete()
        self.assertIsNone(response)
