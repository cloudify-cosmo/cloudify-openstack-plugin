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
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.

import time
import uuid

from cloudify import ctx as cfy_ctx
from cloudify import decorators as cfy_decorators
from cloudify import exceptions as cfy_exc
import openstack_plugin_common

VOLUME_DEVICE_NAME = 'volume_device_name'
VOLUME_ID = 'volume_id'
VOLUME_ATTACHMENT_ID = 'attachment_id'

VOLUME_STATUS_CREATING = 'creating'
VOLUME_STATUS_DELETING = 'deleting'
VOLUME_STATUS_AVAILABLE = 'available'
VOLUME_STATUS_IN_USE = 'in-use'
VOLUME_STATUS_ERROR = 'error'
VOLUME_STATUS_ERROR_DELETING = 'error_deleting'
VOLUME_ERROR_STATUSES = (VOLUME_STATUS_ERROR, VOLUME_STATUS_ERROR_DELETING)


@cfy_decorators.operation
@openstack_plugin_common.with_cinder_client
def create(cinder_client, **kwargs):
    resource_id = cfy_ctx.properties['resource_id']
    use_existing = cfy_ctx.properties['use_existing']
    device_name = cfy_ctx.properties['device_name']

    if use_existing:
        volume_id = _get_volume_id(cinder_client, resource_id)
        v = cinder_client.volumes.get(volume_id)
    else:
        volume = {
            'name': resource_id,
        }
        volume.update(cfy_ctx.properties['volume'])
        v = cinder_client.volumes.create(**volume)

    v, status_verified = wait_until_status(
        cinder_client=cinder_client,
        volume_id=v.id,
        status=VOLUME_STATUS_AVAILABLE)

    if not status_verified:
        cfy_ctx.logger.warning(
            "Volume {0} current state: '{1}', "
            "expected state: '{2}'".format(v.id,
                                           v.status,
                                           VOLUME_STATUS_AVAILABLE))

    cfy_ctx.runtime_properties[VOLUME_ID] = v.id
    cfy_ctx.runtime_properties[VOLUME_DEVICE_NAME] = device_name


@cfy_decorators.operation
@openstack_plugin_common.with_cinder_client
def delete(cinder_client, **kwargs):
    volume_id = cfy_ctx.runtime_properties.get(VOLUME_ID)
    cinder_client.volumes.delete(volume_id)
    del cfy_ctx.runtime_properties[VOLUME_ID]


def _get_volume_id(cinder_client, volume_name_or_id):
    if _is_uuid_like(volume_name_or_id):
        return volume_name_or_id
    volume = _get_volume_by_name(volume_name_or_id, cinder_client)
    return volume.id


def _get_volume_by_name(name, cinder_client):
    volumes = cinder_client.volumes.list()
    result = [item for item in volumes if item.name == name]
    if len(result) != 1:
        raise cfy_exc.NonRecoverableError(
            "Multiple volumes match '{0}' name".format(name))
    return result[0]


def _is_uuid_like(val):
    """Returns validation of a value as a UUID.

    For our purposes, a UUID is a canonical form string:
    aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa

    """
    try:
        return str(uuid.UUID(val)) == val
    except (TypeError, ValueError, AttributeError):
        return False


@openstack_plugin_common.with_cinder_client
def wait_until_status(cinder_client, volume_id, status, num_tries=10,
                      timeout=2):
    for _ in range(num_tries):
        volume = cinder_client.volumes.get(volume_id)

        if volume.status in VOLUME_ERROR_STATUSES:
            raise cfy_exc.NonRecoverableError(
                "Volume {0} is in error state".format(volume_id))

        if volume.status == status:
            return volume, True
        time.sleep(timeout)
    return volume, False


def get_attachment_id(volume, server_id):
    for attachment in volume.attachments:
        if attachment['server_id'] == server_id:
            return attachment['id']
