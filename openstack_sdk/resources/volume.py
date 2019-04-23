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

# Based on this documentation:
# https://docs.openstack.org/openstacksdk/latest/user/proxies/compute.html.

# Local imports
from openstack_sdk.common import (OpenstackResource, ResourceMixin)


class OpenstackVolume(ResourceMixin, OpenstackResource):
    service_type = 'block_storage'
    resource_type = 'volume'

    def list(self, query=None):
        query = query or {}
        return self.connection.block_storage.volumes(**query)

    def get(self):
        return self._find_volume()

    def find_volume(self, name_or_id=None):
        return self._find_volume(name_or_id)

    def _find_volume(self, name_or_id=None):
        if not name_or_id:
            name_or_id = self.name if not \
                self.resource_id else self.resource_id
        self.logger.debug(
            'Attempting to find this volume: {0}'.format(name_or_id))
        volume = self.find_resource(name_or_id)
        self.logger.debug(
            'Found volume with this result: {0}'.format(volume))
        return volume

    def create(self):
        self.logger.debug(
            'Attempting to create volume with these args: {0}'.format(
                self.config))
        volume = self.connection.block_storage.create_volume(**self.config)
        self.logger.debug(
            'Created volume with this result: {0}'.format(volume))
        return volume

    def delete(self):
        volume = self.get()
        self.logger.debug(
            'Attempting to delete this volume: {0}'.format(volume))
        self.connection.block_storage.delete_volume(volume)


class OpenstackVolumeType(ResourceMixin, OpenstackResource):
    service_type = 'block_storage'
    resource_type = 'type'

    def list(self, query=None):
        query = query or {}
        return self.connection.block_storage.types(**query)

    def get(self):
        return self._find_type()

    def find_type(self, name_or_id=None):
        return self._find_type(name_or_id)

    def _find_type(self, name_or_id=None):
        if not name_or_id:
            name_or_id = self.name if not \
                self.resource_id else self.resource_id
        self.logger.debug(
            'Attempting to find this volume type: {0}'
            ''.format(self.resource_id))
        volume_type = self.find_resource(name_or_id)
        self.logger.debug(
            'Found volume type with this result: {0}'.format(volume_type))
        return volume_type

    def create(self):
        self.logger.debug(
            'Attempting to create volume type with these args: {0}'.format(
                self.config))
        volume_type = self.connection.block_storage.create_type(**self.config)
        self.logger.debug(
            'Created volume type with this result: {0}'.format(volume_type))
        return volume_type

    def delete(self):
        volume_type = self.get()
        self.logger.debug(
            'Attempting to delete this volume type: {0}'.format(volume_type))
        self.connection.block_storage.delete_type(volume_type)


class OpenstackVolumeBackup(OpenstackResource):
    resource_type = 'block_storage'
    service_type = 'backup'

    def list(self, query=None):
        query = query or {}
        self.logger.debug('Attempting to list backups')
        result = self.connection.block_storage.backups(query)
        return result

    def get(self):
        self.logger.debug(
            'Attempting to find this backup: {0}'.format(self.resource_id))
        backup = self.connection.block_storage.get_backup(self.resource_id)
        self.logger.debug(
            'Found backup with this result: {0}'.format(backup))
        return backup

    def create(self):
        self.logger.debug(
            'Attempting to create backup with these args: {0}'.format(
                self.config))
        volume = self.connection.block_storage.create_backup(**self.config)
        self.logger.debug(
            'Created backup with this result: {0}'.format(volume))
        return volume

    def restore(self, backup_id, volume_id, name):
        self.logger.debug(
            'Attempting to restore backup this volume: {0}'.format(volume_id))
        result = \
            self.connection.block_storage.restore_backup(backup_id,
                                                         volume_id,
                                                         name)
        self.logger.debug(
            'Restored backup volume with this result: {0}'.format(result))
        return result

    def delete(self):
        volume = self.get()
        self.logger.debug(
            'Attempting to delete this backup: {0}'.format(volume))
        self.connection.block_storage.delete_backup(volume)


class OpenstackVolumeSnapshot(OpenstackResource):
    resource_type = 'block_storage'
    service_type = 'snapshot'

    def list(self, query=None):
        query = query or {}
        self.logger.debug('Attempting to list snapshots')
        result = self.connection.block_storage.snapshots(query)
        return result

    def get(self):
        self.logger.debug(
            'Attempting to find this snapshot: {0}'.format(self.resource_id))
        snapshot = self.connection.block_storage.get_snapshot(self.resource_id)
        self.logger.debug(
            'Found snapshot with this result: {0}'.format(snapshot))
        return snapshot

    def create(self):
        self.logger.debug(
            'Attempting to create snapshot with these args: {0}'.format(
                self.config))
        snapshot = self.connection.block_storage.create_snapshot(**self.config)
        self.logger.debug(
            'Created snapshot with this result: {0}'.format(snapshot))
        return snapshot

    def delete(self):
        snapshot = self.get()
        self.logger.debug(
            'Attempting to delete this snapshot: {0}'.format(snapshot))
        self.connection.block_storage.delete_snapshot(snapshot)
