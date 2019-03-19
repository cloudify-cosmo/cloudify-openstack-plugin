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
import openstack.block_storage.v2.backup

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import volume


class VolumeBackupTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(VolumeBackupTestCase, self).setUp()
        self.fake_client = self.generate_fake_openstack_connection('backup')

        self.volume_backup_instance = volume.OpenstackVolumeBackup(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.volume_backup_instance.connection = self.connection

    def test_get_backup(self):
        volume_backup_instance = openstack.block_storage.v2.backup.Backup(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_backup',
            'description': 'volume_backup_description',
            'availability_zone': 'test_availability_zone',
            'status': 'available'

        })
        self.volume_backup_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_backup = \
            mock.MagicMock(return_value=volume_backup_instance)

        response = self.volume_backup_instance.get()
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.name, 'test_backup')

    def test_list_backups(self):
        volume_backups = [
            openstack.block_storage.v2.backup.Backup(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_volume_backup_1',
                'description': 'volume_backup_description',
                'availability_zone': 'test_availability_zone',
                'status': 'available'
            }),
            openstack.block_storage.v2.backup.Backup(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': 'test_volume_backup_2',
                'description': 'volume_backup_description',
                'availability_zone': 'test_availability_zone',
                'status': 'available'
            })
        ]

        self.fake_client.backups = mock.MagicMock(return_value=volume_backups)
        response = self.volume_backup_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_backup(self):
        volume_backup = {
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_volume_backup_1',
            'description': 'volume_backup_description',
            'availability_zone': 'test_availability_zone',
        }
        new_res = openstack.block_storage.v2.backup.Backup(**volume_backup)
        self.volume_backup_instance.config = volume_backup
        self.fake_client.create_backup = mock.MagicMock(return_value=new_res)

        response = self.volume_backup_instance.create()
        self.assertEqual(response.name, volume_backup['name'])

    def test_delete_backup(self):
        volume_backup = openstack.block_storage.v2.backup.Backup(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_volume_backup_1',
            'description': 'volume_backup_description',
            'availability_zone': 'test_availability_zone',
        })

        self.volume_backup_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_backup = mock.MagicMock(
            return_value=volume_backup)
        self.fake_client.delete_backup = mock.MagicMock(return_value=None)

        response = self.volume_backup_instance.delete()
        self.assertIsNone(response)

    def test_restore_backup(self):
        volume_backup = openstack.block_storage.v2.backup.Backup(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_volume_backup_1',
            'description': 'volume_backup_description',
            'availability_zone': 'test_availability_zone',
            'status': 'available'
        })

        self.volume_backup_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'

        self.fake_client.restore_backup = \
            mock.MagicMock(return_value=volume_backup)

        response = self.volume_backup_instance.restore(
            '1', '2', 'test_volume_backup_1')
        self.assertEqual(response.status, 'available')
