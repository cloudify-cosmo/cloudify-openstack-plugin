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

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import shared_file_system


class SharedFileSystemTestCase(base.OpenStackSDKTestBase):

    @mock.patch('manilaclient.v2.client.Client')
    def setUp(self, *_, **__):
        super(SharedFileSystemTestCase, self).setUp()
        self.share_instance = shared_file_system.OpenstackSharedFileSystem(
            client_config=self.client_config,
            resource_config={'size': 1, 'name': 'test_share'},
            logger=mock.MagicMock()
        )
        self.share_instance.connection = \
            self.generate_fake_openstack_connection()

    def generate_fake_openstack_connection(self):
        connection = mock.MagicMock()
        shares_connection = mock.MagicMock()

        get_response = mock.MagicMock(
            id='a95b5509-c122-4c2f-823e-884bb559afe8',
            resource_id='a95b5509-c122-4c2f-823e-884bb559afe8')
        get_response.name = 'test_share'
        get_response.update.return_value = get_response
        get_response.delete.return_value = (get_response, {})

        get_response.allow.return_value = get_response
        get_response.deny.return_value = get_response
        get_response.export_locations = [
            '192.168.0.2:/volumes/_'
            'nogroup/a95b5509-c122-4c2f-823e-884bb559afe8']

        shares_connection.get.return_value = get_response

        list_response = [get_response]
        shares_connection.list.return_value = list_response

        shares_connection.create.return_value = get_response

        connection.shares = shares_connection
        return connection

    def test_get_share(self, *_, **__):
        response = self.share_instance.get()
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.name, 'test_share')

    def test_list_shares(self, *_, **__):
        response = self.share_instance.list()
        self.assertEqual(response[0].id,
                         'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response[0].name, 'test_share')

    def test_create_share(self, *_, **__):
        response = self.share_instance.create()
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.name, 'test_share')

    def test_update_share(self, *_, **__):
        response = self.share_instance.update()
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.name, 'test_share')

    def test_delete_share(self, *_, **__):
        response = self.share_instance.delete()
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.name, 'test_share')

    def test_allow_share(self, *_, **__):
        response = self.share_instance.allow(
            access_type='ip', access="192.168.0.0/24", access_level='rw')
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.name, 'test_share')

    def test_deny_share(self, *_, **__):
        response = self.share_instance.deny(
            'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.name, 'test_share')

    def test_get_locations_share(self, *_, **__):
        response = self.share_instance.get_locations()
        self.assertTrue(isinstance(response, list))
