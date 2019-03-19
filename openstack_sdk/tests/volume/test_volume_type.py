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
import openstack.block_storage.v2.type

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import volume


class VolumeTypeTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(VolumeTypeTestCase, self).setUp()
        self.fake_client = \
            self.generate_fake_openstack_connection('volume_type')

        self.volume_type_instance = volume.OpenstackVolumeType(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.volume_type_instance.connection = self.connection

    def test_get_volume_type(self):
        volume_type = openstack.block_storage.v2.type.Type(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_volume_type',
            'extra_specs': {
                'capabilities': 'gpu',
            }
        })
        self.volume_type_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_type = mock.MagicMock(return_value=volume_type)

        response = self.volume_type_instance.get()
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.name, 'test_volume_type')

    def test_list_volume_types(self):
        volume_type_list = [
            openstack.block_storage.v2.type.Type(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_volume_type_1',
                'extra_specs': {
                    'capabilities': 'gpu',
                }

            }),
            openstack.block_storage.v2.type.Type(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': 'test_volume_type_2',
                'extra_specs': {
                    'capabilities': 'gpu',
                }
            })
        ]

        self.fake_client.types = mock.MagicMock(return_value=volume_type_list)
        response = self.volume_type_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_volume_type(self):
        volume_type = {
            'name': 'test_volume_type',
            'extra_specs': {
                'capabilities': 'gpu',
            }
        }
        new_res = openstack.block_storage.v2.type.Type(**volume_type)
        self.volume_type_instance.config = volume_type
        self.fake_client.create_type = mock.MagicMock(return_value=new_res)

        response = self.volume_type_instance.create()
        self.assertEqual(response.name, volume_type['name'])

    def test_delete_volume_type(self):
        volume_type = openstack.block_storage.v2.type.Type(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_volume_type_1',
            'extra_specs': {
                'capabilities': 'gpu',
            }

        })

        self.volume_type_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_type = mock.MagicMock(return_value=volume_type)
        self.fake_client.delete_type = mock.MagicMock(return_value=None)

        response = self.volume_type_instance.delete()
        self.assertIsNone(response)
