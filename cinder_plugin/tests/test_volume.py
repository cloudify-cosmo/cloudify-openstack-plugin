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

import contextlib
import mock
import unittest

from cinder_plugin import volume
from nova_plugin import server
import openstack_plugin_common
from cloudify import mocks as cfy_mocks


class TestCinderVolume(unittest.TestCase):

    def test_create_new(self):
        volume_name = 'fake volume name'
        volume_description = 'fake volume'
        volume_id = '00000000-0000-0000-0000-000000000000'
        volume_size = 10

        volume_properties = {
            'volume': {
                'size': volume_size,
                'description': volume_description
            },
            'use_existing': False,
            'device_name': '/dev/fake',
            'resource_id': volume_name,
        }

        creating_volume_m = mock.Mock()
        creating_volume_m.id = volume_id
        creating_volume_m.status = volume.VOLUME_STATUS_CREATING
        available_volume_m = mock.Mock()
        available_volume_m.id = volume_id
        available_volume_m.status = volume.VOLUME_STATUS_AVAILABLE
        cinder_client_m = mock.Mock()
        cinder_client_m.volumes = mock.Mock()
        cinder_client_m.volumes.create = mock.Mock(
            return_value=creating_volume_m)
        cinder_client_m.volumes.get = mock.Mock(
            return_value=available_volume_m)
        ctx_m = cfy_mocks.MockCloudifyContext(properties=volume_properties)

        volume.create(cinder_client=cinder_client_m, ctx=ctx_m)

        cinder_client_m.volumes.create.assert_called_once_with(
            size=volume_size,
            display_name=volume_name,
            description=volume_description)
        cinder_client_m.volumes.get.assert_called_once_with(volume_id)
        self.assertEqual(volume_id,
                         ctx_m.runtime_properties[volume.VOLUME_ID])

    def test_create_use_existing(self):
        volume_id = '00000000-0000-0000-0000-000000000000'

        volume_properties = {
            'use_existing': True,
            'device_name': '/dev/fake',
            'resource_id': volume_id,
        }
        existing_volume_m = mock.Mock()
        existing_volume_m.id = volume_id
        existing_volume_m.status = volume.VOLUME_STATUS_AVAILABLE
        cinder_client_m = mock.Mock()
        cinder_client_m.volumes = mock.Mock()
        cinder_client_m.volumes.get = mock.Mock(
            return_value=existing_volume_m)
        volume_get_calls = [mock.call(volume_id), mock.call(volume_id)]
        ctx_m = cfy_mocks.MockCloudifyContext(properties=volume_properties)

        volume.create(cinder_client=cinder_client_m, ctx=ctx_m)

        cinder_client_m.volumes.get.assert_has_calls(volume_get_calls)
        self.assertEqual(volume_id,
                         ctx_m.runtime_properties[volume.VOLUME_ID])

    def test_delete(self):
        volume_id = '00000000-0000-0000-0000-000000000000'

        volume_properties = {
            'use_existing': False,
        }

        cinder_client_m = mock.Mock()
        cinder_client_m.volumes = mock.Mock()
        cinder_client_m.volumes.delete = mock.Mock()

        ctx_m = cfy_mocks.MockCloudifyContext(properties=volume_properties)
        ctx_m.runtime_properties[volume.VOLUME_ID] = volume_id

        volume.delete(cinder_client=cinder_client_m, ctx=ctx_m)

        cinder_client_m.volumes.delete.assert_called_once_with(volume_id)
        self.assertTrue(volume.VOLUME_ID not in ctx_m.runtime_properties)

    def test_attach(self):
        volume_id = '00000000-0000-0000-0000-000000000000'
        server_id = '11111111-1111-1111-1111-111111111111'
        device_name = '/dev/fake'

        volume_ctx_m = cfy_mocks.MockCloudifyContext()
        volume_ctx_m.runtime_properties[volume.VOLUME_ID] = volume_id
        volume_ctx_m.runtime_properties[volume.VOLUME_DEVICE_NAME] = \
            device_name

        ctx_m = cfy_mocks.MockCloudifyContext(related=volume_ctx_m)
        ctx_m.runtime_properties[server.OPENSTACK_ID_PROPERTY] = server_id

        novaclient_m = mock.Mock()
        novaclient_m.volumes = mock.Mock()
        novaclient_m.volumes.create_server_volume = mock.Mock()

        with contextlib.nested(
            mock.patch.object(
                openstack_plugin_common.NovaClient,
                'get',
                mock.Mock(return_value=novaclient_m)),
            mock.patch.object(
                volume,
                'wait_until_status',
                mock.Mock())):

            server.attach_volume(ctx=ctx_m)

            novaclient_m.volumes.create_server_volume.assert_called_once_with(
                server_id, volume_id, device_name)
            volume.wait_until_status.assert_called_once_with(
                volume_id=volume_id,
                status=volume.VOLUME_STATUS_IN_USE)

    def test_detach(self):
        volume_id = '00000000-0000-0000-0000-000000000000'
        server_id = '11111111-1111-1111-1111-111111111111'
        attachment_id = '22222222-2222-2222-2222-222222222222'

        attachment = {'id': attachment_id,
                      'server_id': server_id,
                      'volume_id': volume_id}

        volume_ctx_m = cfy_mocks.MockCloudifyContext()
        volume_ctx_m.runtime_properties[volume.VOLUME_ID] = volume_id

        ctx_m = cfy_mocks.MockCloudifyContext(related=volume_ctx_m)
        ctx_m.runtime_properties[server.OPENSTACK_ID_PROPERTY] = server_id

        attached_volume_m = mock.Mock()
        attached_volume_m.id = volume_id
        attached_volume_m.status = volume.VOLUME_STATUS_IN_USE
        attached_volume_m.attachments = [attachment]
        cinder_client_m = mock.Mock()
        cinder_client_m.volumes = mock.Mock()
        cinder_client_m.volumes.get = mock.Mock(
            return_value=attached_volume_m)

        novaclient_m = mock.Mock()
        novaclient_m.volumes = mock.Mock()
        novaclient_m.volumes.delete_server_volume = mock.Mock()

        with contextlib.nested(
            mock.patch.object(
                openstack_plugin_common.NovaClient,
                'get',
                mock.Mock(return_value=novaclient_m)),
            mock.patch.object(
                openstack_plugin_common.CinderClient,
                'get',
                mock.Mock(return_value=cinder_client_m)),
            mock.patch.object(
                volume,
                'wait_until_status',
                mock.Mock())):

            server.detach_volume(ctx=ctx_m)

            novaclient_m.volumes.delete_server_volume.assert_called_once_with(
                server_id, attachment_id)
            volume.wait_until_status.assert_called_once_with(
                volume_id=volume_id,
                status=volume.VOLUME_STATUS_AVAILABLE)
