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
import openstack.block_storage.v2.volume

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import volume


class VolumeTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(VolumeTestCase, self).setUp()
        self.fake_client = self.generate_fake_openstack_connection('volume')

        self.volume_instance = volume.OpenstackVolume(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.volume_instance.connection = self.connection

    def test_get_volume(self):
        volume_instance = openstack.block_storage.v2.volume.Volume(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_volume',
            'description': 'volume_description',
            'status': 'available'
        })
        self.volume_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_volume = \
            mock.MagicMock(return_value=volume_instance)

        response = self.volume_instance.get()
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.name, 'test_volume')

    def test_list_volumes(self):
        volumes = [
            openstack.block_storage.v2.volume.Volume(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_volume_1',
                'description': 'volume_description_1',
                'availability_zone': 'test_availability_zone',
                'is_bootable': False,
                'status': 'available'
            }),
            openstack.block_storage.v2.volume.Volume(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': 'test_volume_2',
                'description': 'volume_description_2',
                'availability_zone': 'test_availability_zone',
                'is_bootable': False,
                'status': 'available'
            }),
        ]

        self.fake_client.volumes = mock.MagicMock(return_value=volumes)
        response = self.volume_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_volume(self):
        volume_instance = {
            'name': 'test_volume',
            'description': 'volume_description',
            'size': '12'
        }
        new_res = openstack.block_storage.v2.volume.Volume(**volume_instance)
        self.volume_instance.config = volume_instance
        self.fake_client.create_volume = mock.MagicMock(return_value=new_res)

        response = self.volume_instance.create()
        self.assertEqual(response.name, volume_instance['name'])

    def test_delete_volume(self):
        volume_instance = openstack.block_storage.v2.volume.Volume(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_volume_1',
            'description': 'volume_description_1',
            'availability_zone': 'test_availability_zone',
            'is_bootable': False,
            'status': 'available'
        })

        self.volume_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_volume = mock.MagicMock(
            return_value=volume_instance)
        self.fake_client.delete_volume = mock.MagicMock(return_value=None)

        response = self.volume_instance.delete()
        self.assertIsNone(response)
