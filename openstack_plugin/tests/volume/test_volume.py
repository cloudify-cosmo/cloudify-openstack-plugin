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
import openstack.block_storage.v2.volume
import openstack.block_storage.v2.backup
import openstack.block_storage.v2.snapshot
import openstack.exceptions
from cloudify.exceptions import (OperationRetry,
                                 NonRecoverableError)

# Local imports
from openstack_plugin.tests.base import OpenStackTestBase
from openstack_plugin.resources.volume import volume
from openstack_plugin.utils import get_snapshot_name
from openstack_plugin.constants import (RESOURCE_ID,
                                        IMAGE_NODE_TYPE,
                                        OPENSTACK_NAME_PROPERTY,
                                        OPENSTACK_TYPE_PROPERTY,
                                        IMAGE_OPENSTACK_TYPE,
                                        VOLUME_OPENSTACK_TYPE,
                                        VOLUME_STATUS_CREATING,
                                        VOLUME_STATUS_AVAILABLE,
                                        VOLUME_STATUS_DELETING,
                                        VOLUME_BOOTABLE,
                                        VOLUME_SNAPSHOT_TASK,
                                        VOLUME_BACKUP_ID)


@mock.patch('openstack.connect')
class VolumeTestCase(OpenStackTestBase):

    def setUp(self):
        super(VolumeTestCase, self).setUp()

    @property
    def resource_config(self):
        return {
            'name': 'test_volume',
            'description': 'volume_description',
            'size': '12'
        }

    def test_create(self, mock_connection):
        # Prepare the context for create operation
        rel_specs = [
            {
                'node': {
                    'id': 'image-1',
                    'properties': {
                        'client_config': self.client_config,
                        'resource_config': {
                            'name': 'test-image',
                        }
                    }
                },
                'instance': {
                    'id': 'image-1-efrgsd',
                    'runtime_properties': {
                        RESOURCE_ID: '1',
                        OPENSTACK_TYPE_PROPERTY: IMAGE_OPENSTACK_TYPE,
                        OPENSTACK_NAME_PROPERTY: 'test-image'
                    }
                },
                'type': IMAGE_NODE_TYPE,
            }
        ]
        volume_rels = self.get_mock_relationship_ctx_for_node(rel_specs)

        self._prepare_context_for_operation(
            test_name='VolumeTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.create',
            test_relationships=volume_rels)

        volume_instance = openstack.block_storage.v2.volume.Volume(**{
            'id': '1',
            'name': 'test_volume',
            'description': 'volume_description',
            'status': VOLUME_STATUS_CREATING

        })
        # Mock create volume response
        mock_connection().block_storage.create_volume = \
            mock.MagicMock(return_value=volume_instance)

        # Call create volume
        volume.create()

        self.assertEqual(self._ctx.instance.runtime_properties[RESOURCE_ID],
                         '1')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY],
            'test_volume')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY],
            VOLUME_OPENSTACK_TYPE)

    @mock.patch(
        'openstack_plugin.resources.volume.volume.wait_until_status')
    def test_start(self, mock_wait_status, mock_connection):
        # Prepare the context for start operation
        self._prepare_context_for_operation(
            test_name='VolumeTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.start')

        volume_instance = openstack.block_storage.v2.volume.Volume(**{
            'id': '1',
            'name': 'test_volume',
            'description': 'volume_description',
            'availability_zone': 'test_availability_zone',
            'is_bootable': False,
            'status': VOLUME_STATUS_AVAILABLE

        })
        # Mock get volume response
        mock_connection().block_storage.get_volume = \
            mock.MagicMock(return_value=volume_instance)

        mock_wait_status.return_value = volume_instance

        # Call start volume
        volume.start()

        self.assertEqual(
            self._ctx.instance.runtime_properties[VOLUME_BOOTABLE], False)

        self.assertEqual(
            self._ctx.instance.runtime_properties['availability_zone'],
            'test_availability_zone')

    @mock.patch(
        'openstack_plugin.resources.volume.volume._delete_volume_snapshot')
    def test_delete(self, mock_delete_volume_snapshot, mock_connection):
        # Prepare the context for start operation
        self._prepare_context_for_operation(
            test_name='VolumeTestCase',
            test_runtime_properties={'id': '1'},
            ctx_operation_name='cloudify.interfaces.lifecycle.delete')

        volume_instance = openstack.block_storage.v2.volume.Volume(**{
            'id': '1',
            'name': 'test_volume',
            'description': 'volume_description',
            'availability_zone': 'test_availability_zone',
            'is_bootable': False,
            'status': VOLUME_STATUS_AVAILABLE

        })
        # Mock get volume response
        mock_connection().block_storage.get_volume = \
            mock.MagicMock(side_effect=[volume_instance,
                                        openstack.exceptions.ResourceNotFound])

        # Mock delete volume response
        mock_connection().block_storage.delete_volume = \
            mock.MagicMock(return_value=None)

        # Call delete volume
        volume.delete()

        mock_delete_volume_snapshot.assert_called()

        for attr in [RESOURCE_ID,
                     OPENSTACK_NAME_PROPERTY,
                     OPENSTACK_TYPE_PROPERTY]:
            self.assertNotIn(attr, self._ctx.instance.runtime_properties)

    @mock.patch(
        'openstack_plugin.resources.volume.volume._delete_volume_snapshot')
    def test_delete_retry(self, mock_delete_volume_snapshot, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            test_name='VolumeTestCase',
            test_runtime_properties={'id': '1'},
            ctx_operation_name='cloudify.interfaces.lifecycle.delete')

        volume_instance = openstack.block_storage.v2.volume.Volume(**{
            'id': '1',
            'name': 'test_volume',
            'description': 'volume_description',
            'availability_zone': 'test_availability_zone',
            'is_bootable': False,
            'status': VOLUME_STATUS_AVAILABLE

        })

        volume_instance_deleting = openstack.block_storage.v2.volume.Volume(**{
            'id': '1',
            'name': 'test_volume',
            'description': 'volume_description',
            'availability_zone': 'test_availability_zone',
            'is_bootable': False,
            'status': VOLUME_STATUS_DELETING

        })
        # Mock get volume response
        mock_connection().block_storage.get_volume = \
            mock.MagicMock(side_effect=[volume_instance,
                                        volume_instance_deleting])

        # Mock delete volume response
        mock_connection().block_storage.delete_volume = \
            mock.MagicMock(return_value=None)

        with self.assertRaises(OperationRetry):
            # Call delete volume
            volume.delete()
            mock_delete_volume_snapshot.assert_called()

    def test_create_volume_backup(self, mock_connection):
        # Prepare the context for create snapshot operation
        self._prepare_context_for_operation(
            test_name='VolumeTestCase',
            ctx_operation_name='cloudify.interfaces.snapshot.create')

        # Set resource id as runtime properties for volume instance
        self._ctx.instance.runtime_properties['id'] = '1'

        snapshot_name = \
            get_snapshot_name('volume', 'test_volume_backup', False)

        volume_backup_instance = openstack.block_storage.v2.backup.Backup(**{
            'id': '1',
            'name': snapshot_name,
            'description': 'volume_backup_description',
            'availability_zone': 'test_availability_zone',
            'status': VOLUME_STATUS_CREATING

        })
        available_volume_backup = \
            openstack.block_storage.v2.backup.Backup(**{
                'id': '1',
                'name': snapshot_name,
                'description': 'volume_backup_description',
                'availability_zone': 'test_availability_zone',
                'status': VOLUME_STATUS_AVAILABLE
            })
        # Mock create volume backup response
        mock_connection().block_storage.create_backup = \
            mock.MagicMock(return_value=volume_backup_instance)

        # Mock get volume backup response
        mock_connection().block_storage.get_backup = \
            mock.MagicMock(return_value=available_volume_backup)

        snapshot_params = {
            'snapshot_name': 'test_volume_backup',
            'snapshot_incremental': False
        }

        # Call create backup volume volume
        volume.snapshot_create(**snapshot_params)

        for attr in [VOLUME_SNAPSHOT_TASK, VOLUME_BACKUP_ID]:
            self.assertNotIn(attr, self._ctx.instance.runtime_properties)

    def test_create_volume_backup_with_retry(self, mock_connection):
        # Prepare the context for create snapshot operation
        self._prepare_context_for_operation(
            test_name='VolumeTestCase',
            ctx_operation_name='cloudify.interfaces.snapshot.create')

        # Set resource id as runtime properties for volume instance
        self._ctx.instance.runtime_properties['id'] = '1'

        snapshot_name = \
            get_snapshot_name('volume', 'test_volume_backup', False)

        volume_backup_instance = openstack.block_storage.v2.backup.Backup(**{
            'id': '1',
            'name': snapshot_name,
            'description': 'volume_backup_description',
            'availability_zone': 'test_availability_zone',
            'status': VOLUME_STATUS_CREATING

        })
        # Mock create volume backup response
        mock_connection().block_storage.create_backup = \
            mock.MagicMock(return_value=volume_backup_instance)

        # Mock get volume backup response
        mock_connection().block_storage.get_backup = \
            mock.MagicMock(return_value=volume_backup_instance)

        snapshot_params = {
            'snapshot_name': 'test_volume_backup',
            'snapshot_incremental': False
        }

        # Call create backup volume volume
        with self.assertRaises(OperationRetry):
            volume.snapshot_create(**snapshot_params)

    def test_create_volume_snapshot(self, mock_connection):
        # Prepare the context for create snapshot operation
        self._prepare_context_for_operation(
            test_name='VolumeTestCase',
            ctx_operation_name='cloudify.interfaces.snapshot.create')

        # Set resource id as runtime properties for volume instance
        self._ctx.instance.runtime_properties['id'] = '1'

        snapshot_name = \
            get_snapshot_name('volume', 'test_volume_snapshot', True)

        volume_snapshot_instance = \
            openstack.block_storage.v2.snapshot.Snapshot(**{
                'id': '1',
                'name': snapshot_name,
                'description': 'volume_snapshot_description',
                'status': VOLUME_STATUS_CREATING
            })
        available_volume_snapshot = \
            openstack.block_storage.v2.backup.Backup(**{
                'id': '1',
                'name': snapshot_name,
                'description': 'volume_snapshot_description',
                'status': VOLUME_STATUS_AVAILABLE
            })
        # Mock create volume snapshot response
        mock_connection().block_storage.create_snapshot = \
            mock.MagicMock(return_value=volume_snapshot_instance)

        # Mock get volume snapshot response
        mock_connection().block_storage.get_snapshot = \
            mock.MagicMock(return_value=available_volume_snapshot)

        snapshot_params = {
            'snapshot_name': 'test_volume_snapshot',
            'snapshot_type': 'Daily',
            'snapshot_incremental': True
        }

        # Call create snapshot volume volume
        volume.snapshot_create(**snapshot_params)

        for attr in [VOLUME_SNAPSHOT_TASK, VOLUME_BACKUP_ID]:
            self.assertNotIn(attr, self._ctx.instance.runtime_properties)

    def test_create_volume_snapshot_with_retry(self, mock_connection):
        # Prepare the context for create snapshot operation
        self._prepare_context_for_operation(
            test_name='VolumeTestCase',
            ctx_operation_name='cloudify.interfaces.snapshot.create')

        # Set resource id as runtime properties for volume instance
        self._ctx.instance.runtime_properties['id'] = '1'

        snapshot_name = \
            get_snapshot_name('volume', 'test_volume_snapshot', True)

        volume_snapshot_instance = \
            openstack.block_storage.v2.snapshot.Snapshot(**{
                'id': '1',
                'name': snapshot_name,
                'description': 'volume_snapshot_description',
                'status': VOLUME_STATUS_CREATING
            })
        # Mock create volume snapshot response
        mock_connection().block_storage.create_snapshot = \
            mock.MagicMock(return_value=volume_snapshot_instance)

        # Mock get volume snapshot response
        mock_connection().block_storage.get_snapshot = \
            mock.MagicMock(return_value=volume_snapshot_instance)

        snapshot_params = {
            'snapshot_name': 'test_volume_snapshot',
            'snapshot_type': 'Daily',
            'snapshot_incremental': True
        }

        # Call create snapshot volume volume
        with self.assertRaises(OperationRetry):
            volume.snapshot_create(**snapshot_params)

    def test_restore_volume_backup(self, mock_connection):
        # Prepare the context for apply snapshot operation
        self._prepare_context_for_operation(
            test_name='VolumeTestCase',
            ctx_operation_name='cloudify.interfaces.snapshot.apply')

        # Set resource id as runtime properties for volume instance
        self._ctx.instance.runtime_properties['id'] = '1'

        snapshot_name = \
            get_snapshot_name('volume', 'test_volume_backup', False)

        restored_volume_backup_instance = \
            openstack.block_storage.v2.backup.Backup(**{
                'id': '1',
                'name': snapshot_name,
                'description': 'volume_backup_description',
                'availability_zone': 'test_availability_zone',
                'status': VOLUME_STATUS_CREATING
            })

        volume_backups = [
            openstack.block_storage.v2.backup.Backup(**{
                'id': '1',
                'name': snapshot_name,
                'description': 'volume_backup_description',
                'availability_zone': 'test_availability_zone',
                'status': VOLUME_STATUS_AVAILABLE
            }),
            openstack.block_storage.v2.backup.Backup(**{
                'id': '2',
                'name': 'test_volume_backup_2',
                'description': 'volume_backup_description',
                'availability_zone': 'test_availability_zone',
                'status': VOLUME_STATUS_AVAILABLE
            })
        ]
        # Mock list volume backup response
        mock_connection().block_storage.backups = \
            mock.MagicMock(return_value=volume_backups)

        # Mock restore volume backup response
        mock_connection().block_storage.restore_backup = \
            mock.MagicMock(return_value=restored_volume_backup_instance)

        snapshot_params = {
            'snapshot_name': 'test_volume_backup',
            'snapshot_incremental': False
        }

        # Call restore backup volume volume
        volume.snapshot_apply(**snapshot_params)

    def test_restore_volume_snapshot(self, _):
        # Prepare the context for apply snapshot operation
        self._prepare_context_for_operation(
            test_name='VolumeTestCase',
            ctx_operation_name='cloudify.interfaces.snapshot.apply')

        # Set resource id as runtime properties for volume instance
        self._ctx.instance.runtime_properties['id'] = '1'

        snapshot_params = {
            'snapshot_name': 'test_volume_snapshot',
            'snapshot_incremental': True
        }

        # Call restore snapshot volume volume
        with self.assertRaises(NonRecoverableError):
            volume.snapshot_apply(**snapshot_params)

    def test_delete_volume_backup(self, mock_connection):
        # Prepare the context for delete snapshot operation
        self._prepare_context_for_operation(
            test_name='VolumeTestCase',
            ctx_operation_name='cloudify.interfaces.snapshot.delete')

        # Set resource id as runtime properties for volume instance
        self._ctx.instance.runtime_properties['id'] = '1'

        snapshot_name = \
            get_snapshot_name('volume', 'test_volume_backup', False)

        volume_backup_to_delete = openstack.block_storage.v2.backup.Backup(**{
            'id': '1',
            'name': snapshot_name,
            'description': 'volume_backup_description',
            'availability_zone': 'test_availability_zone',
            'status': VOLUME_STATUS_CREATING

        })

        all_volume_backups = [
            openstack.block_storage.v2.backup.Backup(**{
                'id': '1',
                'name': snapshot_name,
                'description': 'volume_backup_description',
                'availability_zone': 'test_availability_zone',
                'status': VOLUME_STATUS_AVAILABLE
            }),
            openstack.block_storage.v2.backup.Backup(**{
                'id': '2',
                'name': 'test_volume_backup_2',
                'description': 'volume_backup_description',
                'availability_zone': 'test_availability_zone',
                'status': VOLUME_STATUS_AVAILABLE
            })
        ]

        remaining_volume_backups = [
            openstack.block_storage.v2.backup.Backup(**{
                'id': '2',
                'name': 'test_volume_backup_2',
                'description': 'volume_backup_description',
                'availability_zone': 'test_availability_zone',
                'status': VOLUME_STATUS_AVAILABLE
            })
        ]
        # Mock list volume backup response
        mock_connection().block_storage.backups = \
            mock.MagicMock(side_effect=[all_volume_backups,
                                        remaining_volume_backups])

        # Mock get volume backup response
        mock_connection().block_storage.get_backup = \
            mock.MagicMock(return_value=volume_backup_to_delete)

        # Mock delete volume backup response
        mock_connection().block_storage.delete_backup = \
            mock.MagicMock(return_value=None)

        snapshot_params = {
            'snapshot_name': 'test_volume_backup',
            'snapshot_incremental': False
        }

        # Call delete backup volume
        volume.snapshot_delete(**snapshot_params)

    def test_delete_volume_snapshot(self, mock_connection):
        # Prepare the context for delete snapshot operation
        self._prepare_context_for_operation(
            test_name='VolumeTestCase',
            ctx_operation_name='cloudify.interfaces.snapshot.delete')

        # Set resource id as runtime properties for volume instance
        self._ctx.instance.runtime_properties['id'] = '1'

        snapshot_name = \
            get_snapshot_name('volume', 'test_volume_snapshot', True)

        volume_snapshot_to_delete = \
            openstack.block_storage.v2.snapshot.Snapshot(**{
                'id': '1',
                'name': snapshot_name,
                'description': 'volume_backup_description',
                'status': VOLUME_STATUS_CREATING
            })

        all_volume_snapshots = [
            openstack.block_storage.v2.snapshot.Snapshot(**{
                'id': '1',
                'name': snapshot_name,
                'description': 'volume_backup_description',
                'status': VOLUME_STATUS_CREATING
            }),
            openstack.block_storage.v2.snapshot.Snapshot(**{
                'id': '1',
                'name': 'test_volume_snapshot_2',
                'description': 'volume_backup_description',
                'status': VOLUME_STATUS_CREATING
            })
        ]

        remaining_volume_snapshots = [
            openstack.block_storage.v2.snapshot.Snapshot(**{
                'id': '1',
                'name': 'test_volume_snapshot_2',
                'description': 'volume_backup_description',
                'status': VOLUME_STATUS_CREATING
            })
        ]
        # Mock list volume snapshots response
        mock_connection().block_storage.snapshots = \
            mock.MagicMock(side_effect=[all_volume_snapshots,
                                        remaining_volume_snapshots])

        # Mock get volume snapshot response
        mock_connection().block_storage.get_snapshot = \
            mock.MagicMock(return_value=volume_snapshot_to_delete)

        # Mock delete volume snapshot response
        mock_connection().block_storage.delete_snapshot = \
            mock.MagicMock(return_value=None)

        snapshot_params = {
            'snapshot_name': 'test_volume_snapshot',
            'snapshot_incremental': True
        }

        # Call delete snapshot volume
        volume.snapshot_delete(**snapshot_params)

    def test_list_volumes(self, mock_connection):
        # Prepare the context for list volumes operation
        self._prepare_context_for_operation(
            test_name='VolumeTestCase',
            ctx_operation_name='cloudify.interfaces.operations.list')

        volumes = [
            openstack.block_storage.v2.volume.Volume(**{
                'id': '1',
                'name': 'test_volume_1',
                'description': 'volume_description_1',
                'availability_zone': 'test_availability_zone',
                'is_bootable': False,
                'status': VOLUME_STATUS_AVAILABLE
            }),
            openstack.block_storage.v2.volume.Volume(**{
                'id': '2',
                'name': 'test_volume_2',
                'description': 'volume_description_2',
                'availability_zone': 'test_availability_zone',
                'is_bootable': False,
                'status': VOLUME_STATUS_AVAILABLE
            }),
        ]

        # Mock list volumes response
        mock_connection().block_storage.volumes = \
            mock.MagicMock(return_value=volumes)

        # Mock find project response
        mock_connection().identity.find_project = \
            mock.MagicMock(return_value=self.project_resource)

        # Call list volumes
        volume.list_volumes()

        # Check if the projects list saved as runtime properties
        self.assertIn(
            'volume_list',
            self._ctx.instance.runtime_properties)

        # Check the size of volume list
        self.assertEqual(
            len(self._ctx.instance.runtime_properties['volume_list']), 2)

    @mock.patch('openstack_sdk.common.OpenstackResource.get_quota_sets')
    def test_creation_validation(self, mock_quota_sets, mock_connection):
        # Prepare the context for creation validation operation
        self._prepare_context_for_operation(
            test_name='VolumeTestCase',
            ctx_operation_name='cloudify.interfaces.validation.creation')

        volumes = [
            openstack.block_storage.v2.volume.Volume(**{
                'id': '1',
                'name': 'test_volume_1',
                'description': 'volume_description_1',
                'availability_zone': 'test_availability_zone',
                'is_bootable': False,
                'status': VOLUME_STATUS_AVAILABLE
            }),
            openstack.block_storage.v2.volume.Volume(**{
                'id': '2',
                'name': 'test_volume_2',
                'description': 'volume_description_2',
                'availability_zone': 'test_availability_zone',
                'is_bootable': False,
                'status': VOLUME_STATUS_AVAILABLE
            }),
        ]

        # Mock list volumes response
        mock_connection().block_storage.volumes = \
            mock.MagicMock(return_value=volumes)

        # Mock the quota size response
        mock_quota_sets.return_value = 20

        # Call creation validation
        volume.creation_validation()
