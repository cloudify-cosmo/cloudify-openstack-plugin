#########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time

from cloudify import ctx
from cloudify.decorators import operation
from cloudify import exceptions as cfy_exc

from openstack_plugin_common import (delete_resource_and_runtime_properties,
                                     with_cinder_client,
                                     use_external_resource,
                                     validate_resource,
                                     add_list_to_runtime_properties,
                                     create_object_dict,
                                     get_openstack_id,
                                     COMMON_RUNTIME_PROPERTIES_KEYS,
                                     OPENSTACK_AZ_PROPERTY,
                                     OPENSTACK_ID_PROPERTY,
                                     OPENSTACK_TYPE_PROPERTY,
                                     OPENSTACK_NAME_PROPERTY)
from glance_plugin.image import handle_image_from_relationship

VOLUME_STATUS_CREATING = 'creating'
VOLUME_STATUS_DELETING = 'deleting'
VOLUME_STATUS_AVAILABLE = 'available'
VOLUME_STATUS_IN_USE = 'in-use'
VOLUME_STATUS_ERROR = 'error'
VOLUME_STATUS_ERROR_DELETING = 'error_deleting'
VOLUME_ERROR_STATUSES = (VOLUME_STATUS_ERROR, VOLUME_STATUS_ERROR_DELETING)

# Note: The 'device_name' property should actually be a property of the
# relationship between a server and a volume; It'll move to that
# relationship type once relationship properties are better supported.
DEVICE_NAME_PROPERTY = 'device_name'

VOLUME_OPENSTACK_TYPE = 'volume'
VOLUME_OPENSTACK_ID_KEY = 'name'
VOLUME_BOOTABLE = 'bootable'

RUNTIME_PROPERTIES_KEYS = COMMON_RUNTIME_PROPERTIES_KEYS


def _set_volume_runtime_properties(volume):

    try:
        ctx.instance.runtime_properties[OPENSTACK_AZ_PROPERTY] = \
            volume.availability_zone
    except AttributeError:
        ctx.logger.error('Volume availability_zone not found.')

    ctx.instance.runtime_properties[VOLUME_BOOTABLE] = \
        ctx.node.properties.get('boot', False)


@operation(resumable=True)
@with_cinder_client
def create(cinder_client,
           args={},
           status_timeout=15,
           status_attempts=20,
           **kwargs):

    external_volume = use_external_resource(
        ctx, cinder_client, VOLUME_OPENSTACK_TYPE, VOLUME_OPENSTACK_ID_KEY)

    if external_volume:
        _set_volume_runtime_properties(external_volume)
        return

    volume_dict = create_object_dict(ctx, VOLUME_OPENSTACK_TYPE, args, {})
    handle_image_from_relationship(volume_dict, 'imageRef', ctx)

    v = cinder_client.volumes.create(**volume_dict)

    ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY] = v.id
    ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY] = \
        VOLUME_OPENSTACK_TYPE
    ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY] = \
        volume_dict[VOLUME_OPENSTACK_ID_KEY]
    wait_until_status(cinder_client=cinder_client,
                      volume_id=v.id,
                      status=VOLUME_STATUS_AVAILABLE,
                      num_tries=status_attempts,
                      timeout=status_timeout,
                      )
    _set_volume_runtime_properties(v)


def _delete_snapshot(cinder_client, search_opts):
    snapshots = cinder_client.volume_snapshots.list(search_opts=search_opts)
    # no snapshots
    if not snapshots:
        return

    for snapshot in snapshots:
        ctx.logger.debug("Check snapshot before delete: {}:{} with state {}"
                         .format(snapshot.id, snapshot.name, snapshot.status))
        if search_opts.get('display_name'):
            if snapshot.name != search_opts['display_name']:
                continue
        if snapshot.status == 'available':
            snapshot.delete()

    # wait 10 seconds before next check
    time.sleep(10)

    snapshots = cinder_client.volume_snapshots.list(search_opts=search_opts)
    for snapshot in snapshots:
        ctx.logger.debug("Check snapshot after delete: {}:{} with state {}"
                         .format(snapshot.id, snapshot.name, snapshot.status))
        if search_opts.get('display_name'):
            if snapshot.name == search_opts['display_name']:
                return ctx.operation.retry(
                    message='{} is still alive'.format(snapshot.name),
                    retry_after=30)


def _delete_backup(cinder_client, search_opts):
    backups = cinder_client.backups.list(search_opts=search_opts)

    if not backups:
        return

    for backup in backups:
        if search_opts.get(VOLUME_OPENSTACK_ID_KEY):
            if backup.name != search_opts[VOLUME_OPENSTACK_ID_KEY]:
                continue
            ctx.logger.debug("Check backup before delete: {}:{} with state {}"
                             .format(backup.id, backup.name, backup.status))
            if backup.status == 'available':
                backup.delete()

    # wait 10 seconds before next check
    time.sleep(10)

    backups = cinder_client.backups.list(search_opts=search_opts)

    for backup in backups:
        ctx.logger.debug("Check backup after delete: {}:{} with state {}"
                         .format(backup.id, backup.name, backup.status))
        if search_opts.get(VOLUME_OPENSTACK_ID_KEY):
            if backup.name == search_opts[VOLUME_OPENSTACK_ID_KEY]:
                return ctx.operation.retry(
                    message='{} is still alive'.format(backup.name),
                    retry_after=30)


@operation(resumable=True)
@with_cinder_client
def delete(cinder_client, **kwargs):
    # seach snapshots for volume
    search_opts = {
        'volume_id': get_openstack_id(ctx),
    }
    _delete_snapshot(cinder_client, search_opts)
    # remove volume itself
    delete_resource_and_runtime_properties(ctx, cinder_client,
                                           RUNTIME_PROPERTIES_KEYS)


@with_cinder_client
def wait_until_status(cinder_client, volume_id, status, num_tries,
                      timeout):
    for _ in range(num_tries):
        volume = cinder_client.volumes.get(volume_id)

        if volume.status in VOLUME_ERROR_STATUSES:
            raise cfy_exc.NonRecoverableError(
                "Volume {0} is in error state".format(volume_id))

        if volume.status == status:
            return volume, True
        time.sleep(timeout)

    ctx.logger.warning("Volume {0} current state: '{1}', "
                       "expected state: '{2}'".format(volume_id,
                                                      volume.status,
                                                      status))
    return volume, False


@with_cinder_client
def get_attachment(cinder_client, volume_id, server_id):
    volume = cinder_client.volumes.get(volume_id)
    for attachment in volume.attachments:
        if attachment['server_id'] == server_id:
            return attachment


def _get_snapshot_name(ctx, kwargs):
    return "vol-{}-{}".format(get_openstack_id(ctx), kwargs["snapshot_name"])


@with_cinder_client
def snapshot_create(cinder_client, **kwargs):
    volume_id = get_openstack_id(ctx)

    backup_name = _get_snapshot_name(ctx, kwargs)

    snapshot_incremental = kwargs["snapshot_incremental"]
    if not snapshot_incremental:
        ctx.logger.info("Backup create: {}".format(backup_name))
        cinder_client.backups.create(volume_id, name=backup_name)
    else:
        ctx.logger.info("Snapshot create: {}".format(backup_name))
        description = kwargs.get("snapshot_type", "")
        cinder_client.volume_snapshots.create(volume_id,
                                              force=True,
                                              name=backup_name,
                                              description=description,
                                              metadata=None)


@with_cinder_client
def snapshot_apply(cinder_client, **kwargs):
    volume_id = get_openstack_id(ctx)

    backup_name = _get_snapshot_name(ctx, kwargs)
    snapshot_incremental = kwargs["snapshot_incremental"]
    if not snapshot_incremental:
        ctx.logger.info("Backup apply {} to {}".format(backup_name, volume_id))
        search_opts = {
            'volume_id': volume_id,
            VOLUME_OPENSTACK_ID_KEY: backup_name
        }

        backups = cinder_client.backups.list(
            search_opts=search_opts)

        for backup in backups:
            # if returned more than one backup, use first
            if backup.name == backup_name:
                ctx.logger.debug("Used first with {} to {}"
                                 .format(backup.id, volume_id))
                cinder_client.restores.restore(backup.id, volume_id)
                break
        else:
            raise cfy_exc.NonRecoverableError("No such {} backup."
                                              .format(backup_name))
    else:
        ctx.logger.error("Apply snapshot is unsuported")


@with_cinder_client
def snapshot_delete(cinder_client, **kwargs):
    volume_id = get_openstack_id(ctx)

    backup_name = _get_snapshot_name(ctx, kwargs)
    snapshot_incremental = kwargs["snapshot_incremental"]
    if not snapshot_incremental:
        ctx.logger.info("Backup for remove: {}".format(backup_name))
        # search snaphot for delete
        search_opts = {
            'volume_id': volume_id,
            VOLUME_OPENSTACK_ID_KEY: backup_name
        }
        _delete_backup(cinder_client, search_opts)
    else:
        ctx.logger.info("Snapshot for remove: {}".format(backup_name))
        # search snaphot for delete
        search_opts = {
            'volume_id': volume_id,
            'display_name': backup_name
        }

        _delete_snapshot(cinder_client, search_opts)


@operation(resumable=True)
@with_cinder_client
def creation_validation(cinder_client, **kwargs):
    validate_resource(ctx, cinder_client, VOLUME_OPENSTACK_TYPE,
                      VOLUME_OPENSTACK_ID_KEY)


@operation(resumable=True)
@with_cinder_client
def list_volumes(cinder_client, args, **kwargs):
    volume_list = cinder_client.volumes.list(**args)
    add_list_to_runtime_properties(ctx, VOLUME_OPENSTACK_TYPE, volume_list)
