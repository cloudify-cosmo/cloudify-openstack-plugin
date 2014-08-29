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

import mock
import unittest

from cinder_plugin import volume
from cloudify import mocks as cfy_mocks


class TestCinderVolume(unittest.TestCase):

    def test_create_new(self):
        volume_name = 'fake volume name'
        volume_description = 'fake volume'
        volume_id = 'fakefake-fake-fake-fake-fakefakefake'
        volume_size = 10

        volume_properties = {
            'volume': {
                'size': volume_size,
                'description': volume_description
            },
            'use_existing': False,
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
            name=volume_name,
            description=volume_description)
        cinder_client_m.volumes.get.assert_called_once_with(volume_id)
        self.assertEqual(volume_id,
                         ctx_m.runtime_properties[volume.VOLUME_ID])

    def test_create_use_existing(self):
        volume_id = 'fakefake-fake-fake-fake-fakefakefake'

        volume_properties = {
            'use_existing': True,
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
        volume_id = 'fakefake-fake-fake-fake-fakefakefake'

        cinder_client_m = mock.Mock()
        cinder_client_m.volumes = mock.Mock()
        cinder_client_m.volumes.delete = mock.Mock()

        ctx_m = cfy_mocks.MockCloudifyContext()
        ctx_m.runtime_properties[volume.VOLUME_ID] = volume_id

        volume.delete(cinder_client=cinder_client_m, ctx=ctx_m)

        cinder_client_m.volumes.delete.assert_called_once_with(volume_id)
        self.assertTrue(volume.VOLUME_ID not in ctx_m.runtime_properties)
