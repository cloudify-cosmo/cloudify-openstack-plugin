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
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.

import contextlib
import mock
import unittest

from cloudify import mocks as cfy_mocks
from cloudify import exceptions as cfy_exc

from cinder_plugin import volume
from nova_plugin import server
from openstack_plugin_common import (CinderClient,
                                     NovaClient,
                                     OPENSTACK_ID_PROPERTY,
                                     OPENSTACK_TYPE_PROPERTY,
                                     OPENSTACK_NAME_PROPERTY)


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
            'use_external_resource': False,
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
        ctx_m = cfy_mocks.MockCloudifyContext(node_id='a',
                                              properties=volume_properties)

        volume.create(cinder_client=cinder_client_m, ctx=ctx_m)

        cinder_client_m.volumes.create.assert_called_once_with(
            size=volume_size,
            display_name=volume_name,
            description=volume_description)
        cinder_client_m.volumes.get.assert_called_once_with(volume_id)
        self.assertEqual(
            volume_id,
            ctx_m.instance.runtime_properties[OPENSTACK_ID_PROPERTY])
        self.assertEqual(
            volume.VOLUME_OPENSTACK_TYPE,
            ctx_m.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY])

    def test_create_use_existing(self):
        volume_id = '00000000-0000-0000-0000-000000000000'

        volume_properties = {
            'use_external_resource': True,
            'device_name': '/dev/fake',
            'resource_id': volume_id,
        }
        existing_volume_m = mock.Mock()
        existing_volume_m.id = volume_id
        existing_volume_m.status = volume.VOLUME_STATUS_AVAILABLE
        cinder_client_m = mock.Mock()
        cinder_client_m.volumes = mock.Mock()
        cinder_client_m.volumes.create = mock.Mock()
        cinder_client_m.cosmo_get_if_exists = mock.Mock(
            return_value=existing_volume_m)
        cinder_client_m.get_id_from_resource = mock.Mock(
            return_value=volume_id)
        ctx_m = cfy_mocks.MockCloudifyContext(node_id='a',
                                              properties=volume_properties)

        volume.create(cinder_client=cinder_client_m, ctx=ctx_m)

        self.assertFalse(cinder_client_m.volumes.create.called)
        self.assertEqual(
            volume_id,
            ctx_m.instance.runtime_properties[OPENSTACK_ID_PROPERTY])
        self.assertEqual(
            volume.VOLUME_OPENSTACK_TYPE,
            ctx_m.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY])

    def test_delete(self):
        volume_id = '00000000-0000-0000-0000-000000000000'
        volume_name = 'test-volume'

        volume_properties = {
            'use_external_resource': False,
        }

        cinder_client_m = mock.Mock()
        cinder_client_m.cosmo_delete_resource = mock.Mock()

        ctx_m = cfy_mocks.MockCloudifyContext(node_id='a',
                                              properties=volume_properties)
        ctx_m.instance.runtime_properties[OPENSTACK_ID_PROPERTY] = volume_id
        ctx_m.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY] = \
            volume.VOLUME_OPENSTACK_TYPE
        ctx_m.instance.runtime_properties[OPENSTACK_NAME_PROPERTY] = \
            volume_name

        volume.delete(cinder_client=cinder_client_m, ctx=ctx_m)

        cinder_client_m.cosmo_delete_resource.assert_called_once_with(
            volume.VOLUME_OPENSTACK_TYPE, volume_id)
        self.assertTrue(
            OPENSTACK_ID_PROPERTY not in ctx_m.instance.runtime_properties)
        self.assertTrue(OPENSTACK_TYPE_PROPERTY
                        not in ctx_m.instance.runtime_properties)
        self.assertTrue(OPENSTACK_NAME_PROPERTY
                        not in ctx_m.instance.runtime_properties)

    def test_attach(self):
        volume_id = '00000000-0000-0000-0000-000000000000'
        server_id = '11111111-1111-1111-1111-111111111111'
        device_name = '/dev/fake'

        volume_ctx = cfy_mocks.MockContext({
            'node': cfy_mocks.MockContext({
                'properties': {volume.DEVICE_NAME_PROPERTY: device_name}
            }),
            'instance': cfy_mocks.MockContext({
                'runtime_properties': {
                    OPENSTACK_ID_PROPERTY: volume_id,
                }
            })
        })
        server_ctx = cfy_mocks.MockContext({
            'node': cfy_mocks.MockContext({
                'properties': {}
            }),
            'instance': cfy_mocks.MockContext({
                'runtime_properties': {
                    server.OPENSTACK_ID_PROPERTY: server_id
                }
            })
        })

        ctx_m = cfy_mocks.MockCloudifyContext(node_id='a',
                                              target=server_ctx,
                                              source=volume_ctx)

        cinderclient_m = mock.Mock()
        novaclient_m = mock.Mock()
        novaclient_m.volumes = mock.Mock()
        novaclient_m.volumes.create_server_volume = mock.Mock()

        with contextlib.nested(
                mock.patch.object(NovaClient, 'get',
                                  mock.Mock(return_value=novaclient_m)),
                mock.patch.object(CinderClient, 'get',
                                  mock.Mock(return_value=cinderclient_m)),
                mock.patch.object(volume, 'wait_until_status', mock.Mock(return_value=(None,True)))):

            server.attach_volume(ctx=ctx_m)

            novaclient_m.volumes.create_server_volume.assert_called_once_with(
                server_id, volume_id, device_name)
            volume.wait_until_status.assert_called_once_with(
                cinder_client=cinderclient_m,
                volume_id=volume_id,
                status=volume.VOLUME_STATUS_IN_USE)

    def _test_cleanup_after_attach_fails(self, volume_ctx_mgr):
        volume_id = '00000000-0000-0000-0000-000000000000'
        server_id = '11111111-1111-1111-1111-111111111111'
        attachment_id = '22222222-2222-2222-2222-222222222222'
        device_name = '/dev/fake'

        attachment = {'id': attachment_id,
                      'server_id': server_id,
                      'volume_id': volume_id}

        volume_ctx = cfy_mocks.MockContext({
            'node': cfy_mocks.MockContext({
                'properties': {volume.DEVICE_NAME_PROPERTY: device_name}
            }),
            'instance': cfy_mocks.MockContext({
                'runtime_properties': {
                    OPENSTACK_ID_PROPERTY: volume_id,
                }
            })
        })
        server_ctx = cfy_mocks.MockContext({
            'node': cfy_mocks.MockContext({
                'properties': {}
            }),
            'instance': cfy_mocks.MockContext({
                'runtime_properties': {
                    server.OPENSTACK_ID_PROPERTY: server_id
                }
            })
        })

        ctx_m = cfy_mocks.MockCloudifyContext(node_id='a',
                                              target=server_ctx,
                                              source=volume_ctx)

        attached_volume_m = mock.Mock()
        attached_volume_m.id = volume_id
        attached_volume_m.status = volume.VOLUME_STATUS_IN_USE
        attached_volume_m.attachments = [attachment]
        cinderclient_m = mock.Mock()
        cinderclient_m.volumes = mock.Mock()
        cinderclient_m.volumes.get = mock.Mock(
            return_value=attached_volume_m)
        novaclient_m = mock.Mock()
        novaclient_m.volumes = mock.Mock()
        novaclient_m.volumes.create_server_volume = mock.Mock()

        with contextlib.nested(
                mock.patch.object(NovaClient, 'get',
                                  mock.Mock(return_value=novaclient_m)),
                mock.patch.object(CinderClient, 'get',
                                  mock.Mock(return_value=cinderclient_m)),
                volume_ctx_mgr):

            server.attach_volume(ctx=ctx_m)

            novaclient_m.volumes.create_server_volume.assert_called_once_with(
                server_id, volume_id, device_name)
            volume.wait_until_status.assert_any_call(
                cinder_client=cinderclient_m,
                volume_id=volume_id,
                status=volume.VOLUME_STATUS_IN_USE)
            self.assertEqual(2, volume.wait_until_status.call_count)
            # Cleanup expectations
            novaclient_m.volumes.delete_server_volume.assert_called_once_with(
                server_id, attachment_id)
            volume.wait_until_status.assert_called_with(
                cinder_client=cinderclient_m,
                volume_id=volume_id,
                status=volume.VOLUME_STATUS_AVAILABLE)

    def test_cleanup_after_waituntilstatus_times_out(self):
        self._test_cleanup_after_attach_fails(
            volume_ctx_mgr = mock.patch.object(
                volume,
                'wait_until_status',
                mock.Mock(return_value=(None,False))
            )
        )

    def test_cleanup_after_waituntilstatus_throws_error(self):
        nonRecovErr = cfy_exc.NonRecoverableError('An error state')
        try:
            self._test_cleanup_after_attach_fails(
                volume_ctx_mgr = mock.patch.object(
                    volume,
                    'wait_until_status',
                    mock.Mock(side_effect=nonRecovErr)
                )
            )
            self.fail("Expected to catch the %s exception" % (nonRecovErr,))
        except type(nonRecovErr) as e:
            self.assertEquals(nonRecovErr, e)

    def test_detach(self):
        volume_id = '00000000-0000-0000-0000-000000000000'
        server_id = '11111111-1111-1111-1111-111111111111'
        attachment_id = '22222222-2222-2222-2222-222222222222'

        attachment = {'id': attachment_id,
                      'server_id': server_id,
                      'volume_id': volume_id}

        volume_ctx = cfy_mocks.MockContext({
            'node': cfy_mocks.MockContext({
                'properties': {}
            }),
            'instance': cfy_mocks.MockContext({
                'runtime_properties': {
                    OPENSTACK_ID_PROPERTY: volume_id,
                }
            })
        })
        server_ctx = cfy_mocks.MockContext({
            'node': cfy_mocks.MockContext({
                'properties': {}
            }),
            'instance': cfy_mocks.MockContext({
                'runtime_properties': {
                    server.OPENSTACK_ID_PROPERTY: server_id
                }
            })
        })

        ctx_m = cfy_mocks.MockCloudifyContext(node_id='a',
                                              target=server_ctx,
                                              source=volume_ctx)

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
                mock.patch.object(NovaClient, 'get',
                                  mock.Mock(return_value=novaclient_m)),
                mock.patch.object(CinderClient, 'get',
                                  mock.Mock(return_value=cinder_client_m)),
                mock.patch.object(volume, 'wait_until_status', mock.Mock())):

            server.detach_volume(ctx=ctx_m)

            novaclient_m.volumes.delete_server_volume.assert_called_once_with(
                server_id, attachment_id)
            volume.wait_until_status.assert_called_once_with(
                cinder_client=cinder_client_m,
                volume_id=volume_id,
                status=volume.VOLUME_STATUS_AVAILABLE)
