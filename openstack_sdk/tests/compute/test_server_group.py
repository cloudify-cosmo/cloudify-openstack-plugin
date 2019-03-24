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
import openstack.compute.v2.server_group

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import compute


class ServerGroupTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(ServerGroupTestCase, self).setUp()

        self.fake_client =\
            self.generate_fake_openstack_connection('server_group')

        self.server_group_instance = compute.OpenstackServerGroup(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.server_group_instance.connection = self.connection

    def test_get_server_group(self):
        server_group = openstack.compute.v2.server_group.ServerGroup(**{
            'id': 'a34b5509-d122-4d2f-823e-884bb559afe8',
            'name': 'test_server_group',
            'members': ['server1', 'server2'],
            'metadata': {'k': 'v'},
            'policies': ['anti-affinity'],

        })

        self.server_group_instance.name = 'test_server_group'
        self.server_group_instance.id = 'a34b5509-d122-4d2f-823e-884bb559afe8'
        self.fake_client.get_server_group =\
            mock.MagicMock(return_value=server_group)

        response = self.server_group_instance.get()
        self.assertEqual(response.id, 'a34b5509-d122-4d2f-823e-884bb559afe8')
        self.assertEqual(response.name, 'test_server_group')

    def test_list_server_groups(self):
        server_group_list = [
            openstack.compute.v2.server_group.ServerGroup(**{
                'id': 'a34b5509-d122-4d2f-823e-884bb559afe8',
                'name': 'test_server_group',
                'members': ['server1', 'server2'],
                'metadata': {'k': 'v'},
                'policies': ['anti-affinity'],
            }),
            openstack.compute.v2.server_group.ServerGroup(**{
                'id': 'a34b5509-d122-4d2f-823e-884bb559afe7',
                'name': 'test_server_group',
                'members': ['server2', 'server3'],
                'metadata': {'k': 'v'},
                'policies': ['anti-affinity'],
            }),
        ]

        self.fake_client.server_groups =\
            mock.MagicMock(return_value=server_group_list)
        response = self.server_group_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_server_group(self):
        config = {
            'name': 'test_server_group',
            'policies': ['anti-affinity'],
        }

        server_group = {
            'id': 'a34b5509-d122-4d2f-823e-884bb559afe8',
            'name': 'test_server_group',
            'members': ['server1', 'server2'],
            'metadata': {'k': 'v'},
            'policies': ['anti-affinity'],
        }

        self.server_group_instance.config = config
        new_res = openstack.compute.v2.server_group.ServerGroup(**server_group)
        self.fake_client.create_server_group =\
            mock.MagicMock(return_value=new_res)

        response = self.server_group_instance.create()
        self.assertEqual(response.name, config['name'])

    def test_delete_server_group(self):
        server_group = openstack.compute.v2.server_group.ServerGroup(**{
            'id': 'a34b5509-d122-4d2f-823e-884bb559afe8',
            'name': 'test_server_group',
            'members': ['server1', 'server2'],
            'metadata': {'k': 'v'},
            'policies': ['anti-affinity'],

        })

        self.server_group_instance.resource_id = \
            'a34b5509-d122-4d2f-823e-884bb559afe8'

        self.fake_client.get_server_group = \
            mock.MagicMock(return_value=server_group)

        self.fake_client.delete_server_group =\
            mock.MagicMock(return_value=None)

        response = self.server_group_instance.delete()
        self.assertIsNone(response)
