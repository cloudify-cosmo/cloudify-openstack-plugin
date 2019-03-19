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
import openstack.block_storage.v2.snapshot

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import volume


class VolumeSnapshotTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(VolumeSnapshotTestCase, self).setUp()
        self.fake_client = self.generate_fake_openstack_connection('snapshot')

        self.volume_snapshot_instance = volume.OpenstackVolumeSnapshot(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.volume_snapshot_instance.connection = self.connection

    def test_get_snapshot(self):
        volume_snapshot_instance = \
            openstack.block_storage.v2.snapshot.Snapshot(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_snapshot',
                'description': 'volume_backup_description',
                'status': 'available'
            })
        self.volume_snapshot_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_snapshot = \
            mock.MagicMock(return_value=volume_snapshot_instance)

        response = self.volume_snapshot_instance.get()
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.name, 'test_snapshot')

    def test_list_snapshots(self):
        volume_snapshots = [
            openstack.block_storage.v2.snapshot.Snapshot(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_snapshot_1',
                'description': 'volume_backup_description',
                'status': 'available'
            }),
            openstack.block_storage.v2.snapshot.Snapshot(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': 'test_snapshot_2',
                'description': 'volume_backup_description',
                'status': 'available'
            })
        ]

        self.fake_client.snapshots = \
            mock.MagicMock(return_value=volume_snapshots)
        response = self.volume_snapshot_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_snapshot(self):
        volume_snapshot = {
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_snapshot_1',
            'description': 'volume_backup_description',
        }
        new_res = \
            openstack.block_storage.v2.snapshot.Snapshot(**volume_snapshot)
        self.volume_snapshot_instance.config = volume_snapshot
        self.fake_client.create_snapshot = mock.MagicMock(return_value=new_res)

        response = self.volume_snapshot_instance.create()
        self.assertEqual(response.name, volume_snapshot['name'])

    def test_delete_snapshot(self):
        volume_snapshot = openstack.block_storage.v2.snapshot.Snapshot(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_snapshot_1',
            'description': 'volume_backup_description',
            'status': 'available'
        })

        self.volume_snapshot_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_snapshot = mock.MagicMock(
            return_value=volume_snapshot)
        self.fake_client.delete_snapshot = mock.MagicMock(return_value=None)

        response = self.volume_snapshot_instance.delete()
        self.assertIsNone(response)
