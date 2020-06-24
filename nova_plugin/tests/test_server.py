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

import collections
from os import path
import tempfile

import unittest
import mock

import nova_plugin
from cloudify.test_utils import workflow_test

from openstack_plugin_common import NeutronClientWithSugar, \
    OPENSTACK_TYPE_PROPERTY, OPENSTACK_ID_PROPERTY, OPENSTACK_NAME_PROPERTY
from neutron_plugin.network import NETWORK_OPENSTACK_TYPE
from neutron_plugin.port import PORT_OPENSTACK_TYPE
from nova_plugin.tests.test_relationships import RelationshipsTestBase
from nova_plugin.server import _prepare_server_nics
from novaclient import exceptions as nova_exceptions
from cinder_plugin.volume import VOLUME_OPENSTACK_TYPE, VOLUME_BOOTABLE
from cloudify.exceptions import NonRecoverableError, RecoverableError
from cloudify.state import current_ctx

from cloudify.utils import setup_logger

from cloudify.mocks import (
    MockNodeContext,
    MockContext,
    MockCloudifyContext,
    MockNodeInstanceContext,
    MockRelationshipContext,
    MockRelationshipSubjectContext
)


class TestServer(unittest.TestCase):

    blueprint_path = path.join('resources',
                               'test-start-operation-retry-blueprint.yaml')

    @mock.patch('nova_plugin.server.create')
    @mock.patch('nova_plugin.server._set_network_and_ip_runtime_properties')
    @mock.patch('openstack_plugin_common'
                '._check_valid_resource_id_with_operation',
                autospec=True, return_value=True)
    @workflow_test(blueprint_path, copy_plugin_yaml=True)
    def test_nova_server_lifecycle_start(self, cfy_local, *_):

        test_vars = {
            'counter': 0,
            'server': mock.MagicMock()
        }

        def mock_get_server_by_context(*_):
            s = test_vars['server']
            if test_vars['counter'] == 0:
                s.status = nova_plugin.server.SERVER_STATUS_BUILD
            else:
                s.status = nova_plugin.server.SERVER_STATUS_ACTIVE
            test_vars['counter'] += 1
            return s

        with mock.patch('nova_plugin.server.get_server_by_context',
                        new=mock_get_server_by_context):
            cfy_local.execute('install', task_retries=3)

        self.assertEqual(2, test_vars['counter'])
        self.assertEqual(0, test_vars['server'].start.call_count)

    @workflow_test(blueprint_path, copy_plugin_yaml=True)
    @mock.patch('nova_plugin.server.create')
    @mock.patch('nova_plugin.server._set_network_and_ip_runtime_properties')
    @mock.patch('openstack_plugin_common'
                '._check_valid_resource_id_with_operation',
                autospec=True, return_value=True)
    def test_nova_server_lifecycle_start_after_stop(self, cfy_local, *_):

        test_vars = {
            'counter': 0,
            'server': mock.MagicMock()
        }

        def mock_get_server_by_context(_):
            s = test_vars['server']
            if test_vars['counter'] == 0:
                s.status = nova_plugin.server.SERVER_STATUS_SHUTOFF
            elif test_vars['counter'] == 1:
                setattr(s,
                        nova_plugin.server.OS_EXT_STS_TASK_STATE,
                        nova_plugin.server.SERVER_TASK_STATE_POWERING_ON)
            else:
                s.status = nova_plugin.server.SERVER_STATUS_ACTIVE
            test_vars['counter'] += 1
            test_vars['server'] = s
            return s

        with mock.patch('nova_plugin.server.get_server_by_context',
                        new=mock_get_server_by_context):
            cfy_local.execute('install', task_retries=3)

        self.assertEqual(1, test_vars['server'].start.call_count)
        self.assertEqual(3, test_vars['counter'])

    @workflow_test(blueprint_path, copy_plugin_yaml=True)
    @mock.patch('nova_plugin.server.create')
    @mock.patch('nova_plugin.server._set_network_and_ip_runtime_properties')
    @mock.patch('openstack_plugin_common'
                '._check_valid_resource_id_with_operation',
                autospec=True, return_value=True)
    def test_nova_server_lifecycle_start_unknown_status(self, cfy_local, *_):
        test_vars = {
            'counter': 0,
            'server': mock.MagicMock()
        }

        def mock_get_server_by_context(_):
            s = test_vars['server']
            if test_vars['counter'] == 0:
                s.status = '### unknown-status ###'
            test_vars['counter'] += 1
            test_vars['server'] = s
            return s

        with mock.patch('nova_plugin.server.get_server_by_context',
                        new=mock_get_server_by_context):
            self.assertRaisesRegexp(RuntimeError,
                                    'Unexpected server state',
                                    cfy_local.execute,
                                    'install')

        self.assertEqual(0, test_vars['server'].start.call_count)
        self.assertEqual(1, test_vars['counter'])

    @workflow_test(blueprint_path, copy_plugin_yaml=True)
    @mock.patch('nova_plugin.server.start')
    @mock.patch('nova_plugin.server._handle_image_or_flavor')
    @mock.patch('nova_plugin.server._fail_on_missing_required_parameters')
    @mock.patch('openstack_plugin_common.nova_client')
    def test_nova_server_creation_param_integrity(
            self, cfy_local, mock_nova, *args):
        cfy_local.execute('install', task_retries=0)
        calls = mock_nova.Client.return_value.servers.method_calls
        self.assertEqual(1, len(calls))
        kws = calls[0][2]
        self.assertIn('scheduler_hints', kws)
        self.assertEqual(kws['scheduler_hints'],
                         {'group': 'affinity-group-id'},
                         'expecting \'scheduler_hints\' value to exist')

    @workflow_test(blueprint_path, copy_plugin_yaml=True,
                   inputs={'use_password': True})
    @mock.patch('nova_plugin.server.create')
    @mock.patch('nova_plugin.server._set_network_and_ip_runtime_properties')
    @mock.patch(
        'nova_plugin.server.get_single_connected_node_by_openstack_type',
        autospec=True, return_value=None)
    def test_nova_server_with_use_password(self, cfy_local, *_):

        test_vars = {
            'counter': 0,
            'server': mock.MagicMock()
        }

        tmp_path = tempfile.NamedTemporaryFile(prefix='key_name', mode='w')
        key_path = tmp_path.name

        def mock_get_server_by_context(_):
            s = test_vars['server']
            if test_vars['counter'] == 0:
                s.status = nova_plugin.server.SERVER_STATUS_BUILD
            else:
                s.status = nova_plugin.server.SERVER_STATUS_ACTIVE
            test_vars['counter'] += 1

            def check_agent_key_path(private_key):
                self.assertEqual(private_key, key_path)
                return private_key

            s.get_password = check_agent_key_path
            return s

        with mock.patch('nova_plugin.server.get_server_by_context',
                        mock_get_server_by_context):
            with mock.patch(
                    'cloudify.context.BootstrapContext.'
                    'CloudifyAgent.agent_key_path',
                    new_callable=mock.PropertyMock, return_value=key_path):
                cfy_local.execute('install', task_retries=5)

    def tearDown(self):
        current_ctx.clear()

    def _prepare_mocks(self, nova_instance):
        nova_instance.servers.stop = mock.Mock()
        nova_instance.servers.start = mock.Mock()
        nova_instance.servers.resume = mock.Mock()
        nova_instance.servers.suspend = mock.Mock()

    @mock.patch('openstack_plugin_common.NovaClientWithSugar')
    @mock.patch('time.sleep', mock.Mock())
    def test_stop(self, nova_m):
        nova_instance = nova_m.return_value

        # use external resource
        server_ctx = MockCloudifyContext(
            node_id="node_id",
            node_name="node_name",
            properties={'use_external_resource': True},
            runtime_properties={}
        )
        current_ctx.set(server_ctx)
        nova_plugin.server.stop(ctx=server_ctx)

        # use internal already stoped vm
        server_ctx = self._simplectx()
        server_mock = mock.Mock()
        server_mock.status = nova_plugin.server.SERVER_STATUS_SHUTOFF
        nova_instance.servers.get = mock.Mock(return_value=server_mock)
        nova_plugin.server.stop(ctx=server_ctx)

        # use internal slow stop
        server_ctx = self._simplectx()
        server_mock = mock.Mock()
        server_mock.status = nova_plugin.server.SERVER_STATUS_ACTIVE
        nova_instance.servers.get = mock.Mock(return_value=server_mock)
        self._prepare_mocks(nova_instance)

        nova_plugin.server.stop(ctx=server_ctx)

        nova_instance.servers.stop.assert_has_calls([mock.call(server_mock)])

    @mock.patch('openstack_plugin_common.NovaClientWithSugar')
    @mock.patch('time.sleep', mock.Mock())
    def test_server_stop(self, nova_m):
        nova_instance = nova_m.return_value

        # use internal already stoped vm
        self._simplectx()
        server_mock = mock.Mock()
        server_mock.status = nova_plugin.server.SERVER_STATUS_SHUTOFF
        nova_instance.servers.get = mock.Mock(return_value=server_mock)

        nova_plugin.server._server_stop(nova_instance, server_mock)

        nova_instance.servers.stop.assert_not_called()
        nova_instance.servers.start.assert_not_called()

        # use internal slow stop
        self._simplectx()
        server_mock = mock.Mock()
        server_mock.status = nova_plugin.server.SERVER_STATUS_ACTIVE
        nova_instance.servers.get = mock.Mock(return_value=server_mock)
        self._prepare_mocks(nova_instance)

        nova_plugin.server._server_stop(nova_instance, server_mock)

        nova_instance.servers.stop.assert_has_calls([mock.call(server_mock)])
        nova_instance.servers.start.assert_not_called()

        # stop on first call
        self._simplectx()
        self.func_called = False

        def _server_get(server_id):
            server_mock = mock.Mock()

            if not self.func_called:
                server_mock.status = nova_plugin.server.SERVER_STATUS_ACTIVE
                self.func_called = True
            else:
                server_mock.status = nova_plugin.server.SERVER_STATUS_SHUTOFF
            return server_mock

        nova_instance.servers.get = _server_get
        self._prepare_mocks(nova_instance)

        nova_plugin.server._server_stop(nova_instance, server_mock)

        nova_instance.servers.stop.assert_has_calls([mock.call(server_mock)])
        nova_instance.servers.start.assert_not_called()

    @mock.patch('openstack_plugin_common.NovaClientWithSugar')
    @mock.patch('time.sleep', mock.Mock())
    def test_server_start(self, nova_m):
        nova_instance = nova_m.return_value

        # use internal already started vm
        self._simplectx()
        server_mock = mock.Mock()
        server_mock.status = nova_plugin.server.SERVER_STATUS_ACTIVE
        nova_instance.servers.get = mock.Mock(return_value=server_mock)

        nova_plugin.server._server_start(nova_instance, server_mock)

        nova_instance.servers.stop.assert_not_called()
        nova_instance.servers.start.assert_not_called()

        # use internal slow start
        self._simplectx()
        server_mock = mock.Mock()
        server_mock.status = nova_plugin.server.SERVER_STATUS_SHUTOFF
        nova_instance.servers.get = mock.Mock(return_value=server_mock)
        self._prepare_mocks(nova_instance)

        nova_plugin.server._server_start(nova_instance, server_mock)

        nova_instance.servers.start.assert_has_calls([mock.call(server_mock)])
        nova_instance.servers.stop.assert_not_called()

        # start on first call
        self._simplectx()
        self.func_called = False

        def _server_get(server_id):
            server_mock = mock.Mock()

            if not self.func_called:
                server_mock.status = nova_plugin.server.SERVER_STATUS_SHUTOFF
                self.func_called = True
            else:
                server_mock.status = nova_plugin.server.SERVER_STATUS_ACTIVE
            return server_mock

        nova_instance.servers.get = _server_get
        self._prepare_mocks(nova_instance)

        nova_plugin.server._server_start(nova_instance, server_mock)

        nova_instance.servers.start.assert_has_calls([mock.call(server_mock)])
        nova_instance.servers.stop.assert_not_called()

    @mock.patch('openstack_plugin_common.NovaClientWithSugar')
    @mock.patch('time.sleep', mock.Mock())
    def test_server_reboot(self, nova_m):
        ctx_operation = {
            'retry_number': 0
        }
        nova_instance = nova_m.return_value

        # use internal already started vm
        self._simplectx(operation=ctx_operation)
        server_mock = mock.Mock()
        server_mock.status = nova_plugin.server.SERVER_STATUS_ACTIVE
        nova_instance.servers.get = mock.Mock(return_value=server_mock)

        nova_plugin.server.reboot(reboot_type='soft')

        nova_instance.servers.stop.assert_not_called()
        nova_instance.servers.start.assert_not_called()
        nova_instance.servers.reboot.assert_has_calls(
            [mock.call(server_mock, 'SOFT')])

        # use internal already started vm
        self._simplectx(operation=ctx_operation)
        server_mock = mock.Mock()
        server_mock.status = nova_plugin.server.SERVER_STATUS_ACTIVE
        nova_instance.servers.get = mock.Mock(return_value=server_mock)

        nova_plugin.server.reboot(reboot_type='hard')

        nova_instance.servers.stop.assert_not_called()
        nova_instance.servers.start.assert_not_called()
        nova_instance.servers.reboot.assert_has_calls(
            [mock.call(server_mock, 'HARD')])

    @mock.patch('openstack_plugin_common.NovaClientWithSugar')
    @mock.patch('time.sleep', mock.Mock())
    def test_server_resume(self, nova_m):
        nova_instance = nova_m.return_value

        # use internal already resumed vm
        self._simplectx()
        server_mock = mock.Mock()
        server_mock.status = nova_plugin.server.SERVER_STATUS_ACTIVE
        nova_instance.servers.get = mock.Mock(return_value=None)

        nova_plugin.server._server_resume(nova_instance, server_mock)

        nova_instance.servers.get.assert_not_called()
        nova_instance.servers.stop.assert_not_called()
        nova_instance.servers.start.assert_not_called()

        # use internal run resume
        self._simplectx()
        server_mock = mock.Mock()
        server_mock.status = nova_plugin.server.SERVER_STATUS_SUSPENDED
        nova_instance.servers.get = mock.Mock(return_value=server_mock)
        self._prepare_mocks(nova_instance)

        nova_plugin.server._server_resume(nova_instance, server_mock)

        nova_instance.servers.resume.assert_has_calls([mock.call(server_mock)])
        nova_instance.servers.stop.assert_not_called()
        nova_instance.servers.get.assert_not_called()
        nova_instance.servers.start.assert_not_called()
        nova_instance.servers.stop.assert_not_called()

    @mock.patch('openstack_plugin_common.NovaClientWithSugar')
    @mock.patch('time.sleep', mock.Mock())
    def test_server_suspend(self, nova_m):
        nova_instance = nova_m.return_value

        # use internal already resumed vm
        self._simplectx()
        server_mock = mock.Mock()
        server_mock.status = nova_plugin.server.SERVER_STATUS_SUSPENDED
        nova_instance.servers.get = mock.Mock(return_value=None)

        nova_plugin.server._server_suspend(nova_instance, server_mock)

        nova_instance.servers.get.assert_not_called()
        nova_instance.servers.stop.assert_not_called()
        nova_instance.servers.start.assert_not_called()

        # use internal run resume
        self._simplectx()
        server_mock = mock.Mock()
        server_mock.status = nova_plugin.server.SERVER_STATUS_ACTIVE
        nova_instance.servers.get = mock.Mock(return_value=server_mock)
        self._prepare_mocks(nova_instance)

        nova_plugin.server._server_suspend(nova_instance, server_mock)

        nova_instance.servers.suspend.assert_has_calls(
            [mock.call(server_mock)])
        nova_instance.servers.resume.assert_not_called()
        nova_instance.servers.stop.assert_not_called()
        nova_instance.servers.get.assert_not_called()
        nova_instance.servers.start.assert_not_called()
        nova_instance.servers.stop.assert_not_called()

    @mock.patch('openstack_plugin_common.NovaClientWithSugar')
    @mock.patch('time.sleep', mock.Mock())
    def test_freeze_suspend(self, nova_m):
        nova_instance = nova_m.return_value

        # use internal already suspended vm
        server_ctx = self._simplectx()
        server_mock = mock.Mock()
        server_mock.status = nova_plugin.server.SERVER_STATUS_SUSPENDED
        nova_instance.servers.get = mock.Mock(return_value=server_mock)
        nova_plugin.server.freeze_suspend(ctx=server_ctx)

    @mock.patch('openstack_plugin_common.NovaClientWithSugar')
    @mock.patch('time.sleep', mock.Mock())
    def test_freeze_resume(self, nova_m):
        nova_instance = nova_m.return_value

        # use internal already resumed vm
        server_ctx = self._simplectx()
        server_mock = mock.Mock()
        server_mock.status = nova_plugin.server.SERVER_STATUS_ACTIVE
        nova_instance.servers.get = mock.Mock(return_value=server_mock)
        nova_plugin.server.freeze_resume(ctx=server_ctx)

    @mock.patch('openstack_plugin_common.NovaClientWithSugar')
    @mock.patch('time.sleep', mock.Mock())
    def test_check_finished_upload(self, nova_m):
        nova_instance = nova_m.return_value

        # ready for actions
        self._simplectx()
        server_mock = mock.Mock()
        server_mock.id = 'server_id'
        setattr(server_mock, nova_plugin.server.OS_EXT_STS_TASK_STATE,
                'ready')
        nova_instance.servers.get = mock.Mock(return_value=server_mock)

        nova_plugin.server._check_finished_upload(nova_instance, server_mock,
                                                  ['image_uploading'])

        # still uploading
        setattr(server_mock, nova_plugin.server.OS_EXT_STS_TASK_STATE,
                'image_uploading')

        nova_plugin.server._check_finished_upload(nova_instance, server_mock,
                                                  ['image_uploading'])

    def _simplectx(self, operation=None):
        server_ctx = MockCloudifyContext(
            deployment_id='deployment_id',
            node_id="node_id",
            node_name="node_name",
            properties={},
            operation=operation,
            runtime_properties={'external_id': 'server_id'}
        )
        current_ctx.set(server_ctx)
        return server_ctx

    @mock.patch('openstack_plugin_common.NovaClientWithSugar')
    @mock.patch('openstack_plugin_common.GlanceClientWithSugar')
    @mock.patch('time.sleep', mock.Mock())
    def test_snapshot_create(self, glance_m, nova_m):
        nova_instance = nova_m.return_value
        glance_instance = glance_m.return_value

        server_ctx = self._simplectx()

        # snapshot
        server_mock = mock.Mock()
        server_mock.backup = mock.Mock()
        server_mock.create_image = mock.Mock()
        server_mock.id = 'server_id'
        setattr(server_mock, nova_plugin.server.OS_EXT_STS_TASK_STATE,
                'ready')
        nova_instance.servers.get = mock.Mock(return_value=server_mock)
        glance_instance.images.list = mock.Mock(return_value=[])

        with mock.patch('openstack_plugin_common._find_context_in_kw',
                        mock.Mock(return_value=server_ctx)):
            nova_plugin.server.snapshot_create(ctx=server_ctx,
                                               snapshot_name='snapshot_name',
                                               snapshot_rotation=10,
                                               snapshot_incremental=True,
                                               snapshot_type='week')

        nova_instance.servers.get.assert_has_calls(
            [mock.call('server_id')] * 3)
        server_mock.create_image.assert_called_once_with(
            'vm-server_id-snapshot_name-increment')
        server_mock.backup.assert_not_called()

        # backup
        server_mock = mock.Mock()
        server_mock.backup = mock.Mock()
        server_mock.create_image = mock.Mock()
        server_mock.id = 'server_id'
        setattr(server_mock, nova_plugin.server.OS_EXT_STS_TASK_STATE,
                'ready')
        nova_instance.servers.get = mock.Mock(return_value=server_mock)
        glance_instance.images.list = mock.Mock(return_value=[])

        with mock.patch('openstack_plugin_common._find_context_in_kw',
                        mock.Mock(return_value=server_ctx)):
            nova_plugin.server.snapshot_create(ctx=server_ctx,
                                               snapshot_name='snapshot_name',
                                               snapshot_rotation=10,
                                               snapshot_incremental=False,
                                               snapshot_type='week')

        nova_instance.servers.get.assert_has_calls(
            [mock.call('server_id')] * 3)
        server_mock.create_image.assert_not_called()
        server_mock.backup.assert_called_once_with(
            'vm-server_id-snapshot_name-backup', 'week', 10)
        glance_instance.images.list.assert_called_once_with(filters={
            'name': 'vm-server_id-snapshot_name-backup'})

        # we already has such backup
        glance_instance.images.list = mock.Mock(return_value=[{
            'name': 'others',
            'image_type': 'raw',
            'id': 'a',
            'status': 'active'
        }, {
            'name': 'vm-server_id-snapshot_name-backup',
            'image_type': 'raw',
            'id': 'b',
            'status': 'active'
        }, {
            'name': 'vm-server_id-snapshot_name-increment',
            'image_type': 'snapshot',
            'id': 'c',
            'status': 'active'
        }, {
            'name': 'vm-server_id-snapshot_name-backup',
            'image_type': 'backup',
            'id': 'd',
            'status': 'active'
        }])
        with mock.patch('openstack_plugin_common._find_context_in_kw',
                        mock.Mock(return_value=server_ctx)):
            with self.assertRaisesRegexp(
                NonRecoverableError,
                "Snapshot vm-server_id-snapshot_name-backup already exists."
            ):
                nova_plugin.server.snapshot_create(
                    ctx=server_ctx, snapshot_name='snapshot_name',
                    snapshot_rotation=10, snapshot_incremental=False,
                    snapshot_type='week')

    @mock.patch('openstack_plugin_common.NovaClientWithSugar')
    @mock.patch('openstack_plugin_common.GlanceClientWithSugar')
    @mock.patch('time.sleep', mock.Mock())
    def test_snapshot_apply(self, glance_m, nova_m):
        nova_instance = nova_m.return_value
        glance_instance = glance_m.return_value

        server_ctx = self._simplectx()

        # snapshot
        server_mock = mock.Mock()
        server_mock.rebuild = mock.Mock()
        server_mock.id = 'server_id'
        setattr(server_mock, nova_plugin.server.OS_EXT_STS_TASK_STATE,
                'ready')
        nova_instance.servers.get = mock.Mock(return_value=server_mock)
        glance_instance.images.list = mock.Mock(return_value=[
            {
                'name': 'vm-server_id-snapshot_name-increment',
                'image_type': 'snapshot',
                'id': 'abc',
                'status': 'active'
            }
        ])

        with mock.patch('openstack_plugin_common._find_context_in_kw',
                        mock.Mock(return_value=server_ctx)):
            nova_plugin.server.snapshot_apply(ctx=server_ctx,
                                              snapshot_name='snapshot_name',
                                              snapshot_incremental=True)

        nova_instance.servers.get.assert_has_calls(
            [mock.call('server_id')] * 3)
        server_mock.rebuild.assert_called_once_with("abc")

        # backup
        with mock.patch('openstack_plugin_common._find_context_in_kw',
                        mock.Mock(return_value=server_ctx)):
            with self.assertRaisesRegexp(
                NonRecoverableError,
                'No snapshots found with name: vm-server_id-snapshot_name.'
            ):
                nova_plugin.server.snapshot_apply(
                    ctx=server_ctx, snapshot_name='snapshot_name',
                    snapshot_incremental=False)

    @mock.patch('openstack_plugin_common.NovaClientWithSugar')
    @mock.patch('time.sleep', mock.Mock())
    def test_image_delete(self, glance_m):
        glance_instance = glance_m.return_value
        server_ctx = self._simplectx()

        # still alive
        glance_instance.images.list = mock.Mock(return_value=[
            {
                'name': 'vm-server_id-snapshot_name-increment',
                'image_type': 'snapshot',
                'id': 'abc',
                'status': 'active'
            }
        ])

        server_ctx.operation.retry = mock.Mock(
            side_effect=RecoverableError())
        with self.assertRaises(RecoverableError):
            nova_plugin.server._image_delete(
                glance_instance,
                snapshot_name='vm-server_id-snapshot_name-increment',
                snapshot_incremental=True)
        server_ctx.operation.retry.assert_called_with(
            message='abc is still alive', retry_after=30)

        # removed
        glance_instance.images.list = mock.Mock(return_value=[])

        nova_plugin.server._image_delete(
            glance_instance, snapshot_name='snapshot_name',
            snapshot_incremental=True)

    @mock.patch('openstack_plugin_common.NovaClientWithSugar')
    @mock.patch('openstack_plugin_common.GlanceClientWithSugar')
    @mock.patch('time.sleep', mock.Mock())
    def test_snapshot_delete(self, glance_m, nova_m):
        nova_instance = nova_m.return_value
        glance_instance = glance_m.return_value

        server_ctx = self._simplectx()

        # snapshot
        server_mock = mock.Mock()
        server_mock.id = 'server_id'
        setattr(server_mock, nova_plugin.server.OS_EXT_STS_TASK_STATE,
                'ready')
        nova_instance.servers.get = mock.Mock(return_value=server_mock)
        glance_instance.images.delete = mock.Mock()
        glance_instance.images.list = mock.Mock(return_value=[
            {
                'name': 'vm-server_id-snapshot_name-increment',
                'image_type': 'snapshot',
                'id': 'abc',
                'status': 'active'
            }
        ])

        server_ctx.operation.retry = mock.Mock(
            side_effect=RecoverableError('still alive'))
        with mock.patch('openstack_plugin_common._find_context_in_kw',
                        mock.Mock(return_value=server_ctx)):
            with self.assertRaisesRegexp(
                RecoverableError,
                'still alive'
            ):
                nova_plugin.server.snapshot_delete(
                    ctx=server_ctx, snapshot_name='snapshot_name',
                    snapshot_incremental=True)
        server_ctx.operation.retry.assert_called_with(
            message='abc is still alive', retry_after=30)

        glance_instance.images.list.assert_has_calls([
            mock.call(filters={"name": "vm-server_id-snapshot_name-increment"})
        ])
        glance_instance.images.delete.assert_called_once_with("abc")

        # backup, if image does not exist - ignore
        with mock.patch('openstack_plugin_common._find_context_in_kw',
                        mock.Mock(return_value=server_ctx)):
            nova_plugin.server.snapshot_delete(
                ctx=server_ctx, snapshot_name='snapshot_name',
                snapshot_incremental=False)

    @mock.patch('openstack_plugin_common.NovaClientWithSugar')
    def test_list_servers(self, nova_m):
        nova_instance = nova_m.return_value
        server_ctx = self._simplectx()

        nova_instance.servers.list = mock.Mock(return_value=[])

        nova_plugin.server.list_servers(ctx=server_ctx, args={"abc": "def"})

        nova_instance.servers.list.assert_called_once_with(abc="def")
        self.assertEqual(
            {'external_id': 'server_id', 'server_list': []},
            server_ctx.instance.runtime_properties
        )

    @mock.patch('openstack_plugin_common.NovaClientWithSugar')
    def test_wait_for_server_to_be_deleted(self, nova_m):
        nova_instance = nova_m.return_value
        self._simplectx()
        # removed
        nova_instance.servers.get = mock.Mock(
            side_effect=nova_exceptions.NotFound("abc"))
        nova_plugin.server._wait_for_server_to_be_deleted(
            nova_instance, "unknown")
        nova_instance.servers.get.assert_called_once_with("unknown")

        # still have
        server_mock = mock.Mock()
        server_mock.id = "a"
        server_mock.status = "b"
        nova_instance.servers.get = mock.Mock(return_value=server_mock)

        fake_time_values = [480, 240, 120, 60, 0]

        def fake_time(*_):
            return fake_time_values.pop()

        with mock.patch('time.time', fake_time):
            with self.assertRaisesRegexp(
                RuntimeError,
                'Server unknown has not been deleted. waited for 120 seconds'
            ):
                nova_plugin.server._wait_for_server_to_be_deleted(
                    nova_instance, "unknown")

    def test_get_properties_by_node_instance_id(self):
        # local run
        ctx = self._simplectx()
        ctx._local = True
        mock_instance = mock.Mock()
        mock_instance.node_id = 'node_id'
        mock_node = mock.Mock()
        mock_node.properties = {'a': 'b'}
        ctx._endpoint.get_node_instance = mock.Mock(return_value=mock_instance)
        ctx._endpoint.get_node = mock.Mock(return_value=mock_node)
        self.assertEqual(
            nova_plugin.server._get_properties_by_node_instance_id('abc'),
            {'a': 'b'}
        )
        ctx._endpoint.get_node_instance.assert_called_once_with('abc')
        ctx._endpoint.get_node.assert_called_once_with('node_id')
        # manager run
        ctx = self._simplectx()
        ctx._local = False
        fake_client = mock.Mock()
        fake_client.node_instances.get = mock.Mock(return_value=mock_instance)
        fake_client.nodes.get = mock.Mock(return_value=mock_node)
        with mock.patch(
            'nova_plugin.server.get_rest_client',
            mock.Mock(return_value=fake_client)
        ):
            self.assertEqual(
                nova_plugin.server._get_properties_by_node_instance_id('abc'),
                {'a': 'b'}
            )
            fake_client.node_instances.get.assert_called_once_with('abc')
            fake_client.nodes.get.assert_called_once_with('deployment_id',
                                                          'node_id')

    @mock.patch('openstack_plugin_common.NovaClientWithSugar')
    def test_validate_external_server_nics(self, _nova_m):
        self._simplectx()
        external_server = mock.Mock()
        external_server.human_id = '_server'

        attached_interface = mock.Mock()
        attached_interface.net_id = 'net1'
        attached_interface.port_id = 'port1'

        external_server.interface_list = mock.Mock(
            return_value=[attached_interface])
        external_server.interface_attach = mock.Mock()

        # Check that we fail if have alredy attached ports
        with self.assertRaises(NonRecoverableError) as error:
            nova_plugin.server._validate_external_server_nics(
                external_server, ['net1'], ['port1'])

        external_server.interface_attach.assert_not_called()
        self.assertEqual(
            str(error.exception),
            "Several ports/networks already connected to external server "
            "_server: Networks - ['net1']; Ports - ['port1']"
        )

        # no attached ports from list
        nova_plugin.server._validate_external_server_nics(
            external_server, ['net2'], ['port2'])
        external_server.interface_attach.assert_has_calls([
            mock.call(port_id='port2', net_id=None, fixed_ip=None),
            mock.call(port_id=None, net_id='net2', fixed_ip=None)
        ])

        # net attached with port
        new_interface = mock.Mock()
        new_interface.net_id = 'net2'
        new_interface.port_id = 'port2'
        results = [
            [new_interface, attached_interface],
            [attached_interface]
        ]

        def _interface_list():
            return results.pop()

        external_server.interface_attach = mock.Mock()
        external_server.interface_list = _interface_list
        nova_plugin.server._validate_external_server_nics(
            external_server, ['net2'], ['port2'])
        external_server.interface_attach.assert_has_calls([
            mock.call(port_id='port2', net_id=None, fixed_ip=None)
        ])

    @mock.patch('openstack_plugin_common.NovaClientWithSugar')
    @mock.patch('openstack_plugin_common.NeutronClientWithSugar')
    def test_external_server_create(self, _neutron_m, _nova_m):
        ctx = self._simplectx()

        external_server = mock.Mock()
        external_server.human_id = '_server'
        external_server.metadata = {}
        external_server.networks = {'abc': ['127.0.0.1']}
        external_server.accessIPv4 = True
        external_server.accessIPv6 = False
        external_server.interface_list = mock.Mock(return_value=[])

        with mock.patch(
            'nova_plugin.server.'
            'get_openstack_ids_of_connected_nodes_by_openstack_type',
            mock.Mock(return_value=[])
        ):
            with mock.patch(
                'nova_plugin.server.'
                'get_openstack_id_of_single_connected_node_by_openstack_type',
                mock.Mock(return_value=None)
            ):
                with mock.patch('openstack_plugin_common._find_context_in_kw',
                                mock.Mock(return_value=ctx)):
                    with mock.patch(
                        'nova_plugin.server.use_external_resource',
                        mock.Mock(return_value=external_server)
                    ):
                        nova_plugin.server.create(args=[])


class TestMergeNICs(unittest.TestCase):
    def test_no_management_network(self):
        mgmt_network_id = None
        nics = [{'net-id': 'other network'}]

        merged = nova_plugin.server._merge_nics(mgmt_network_id, nics)

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]['net-id'], 'other network')

    def test_merge_prepends_management_network(self):
        """When the mgmt network isnt in a relationship, its the 1st nic."""
        mgmt_network_id = 'management network'
        nics = [{'net-id': 'other network'}]

        merged = nova_plugin.server._merge_nics(mgmt_network_id, nics)

        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0]['net-id'], 'management network')

    def test_management_network_in_relationships(self):
        """When the mgmt network was in a relationship, it's not prepended."""
        mgmt_network_id = 'management network'
        nics = [{'net-id': 'other network'}, {'net-id': 'management network'}]

        merged = nova_plugin.server._merge_nics(mgmt_network_id, nics)

        self.assertEqual(nics, merged)


class TestNormalizeNICs(unittest.TestCase):
    def test_normalize_port_priority(self):
        """Whe there's both net-id and port-id, port-id is used."""
        nics = [{'net-id': '1'}, {'port-id': '2'}, {'net-id': 3, 'port-id': 4}]
        normalized = nova_plugin.server._normalize_nics(nics)
        expected = [{'net-id': '1'}, {'port-id': '2'}, {'port-id': 4}]
        self.assertEqual(expected, normalized)


class MockNeutronClient(NeutronClientWithSugar):
    """A fake neutron client with hard-coded test data."""

    @mock.patch('openstack_plugin_common.OpenStackClient.__init__',
                new=mock.Mock())
    def __init__(self):
        super(MockNeutronClient, self).__init__()

    @staticmethod
    def _search_filter(objs, search_params):
        """Mock neutron's filtering by attributes in list_* methods.

        list_* methods (list_networks, list_ports)
        """
        def _matches(obj, search_params):
            return all(obj[k] == v for k, v in search_params.items())
        return [obj for obj in objs if _matches(obj, search_params)]

    def list_networks(self, **search_params):
        networks = [
            {'name': 'network1', 'id': '1'},
            {'name': 'network2', 'id': '2'},
            {'name': 'network3', 'id': '3'},
            {'name': 'network4', 'id': '4'},
            {'name': 'network5', 'id': '5'},
            {'name': 'network6', 'id': '6'},
            {'name': 'other', 'id': 'other'}
        ]
        return {'networks': self._search_filter(networks, search_params)}

    def list_ports(self, **search_params):
        ports = [
            {'name': 'port1', 'id': '1', 'network_id': '1'},
            {'name': 'port2', 'id': '2', 'network_id': '1'},
            {'name': 'port3', 'id': '3', 'network_id': '2'},
            {'name': 'port4', 'id': '4', 'network_id': '2'},
        ]
        return {'ports': self._search_filter(ports, search_params)}

    def show_port(self, port_id):
        ports = self.list_ports(id=port_id)
        return {'port': ports['ports'][0]}


class NICTestBase(RelationshipsTestBase):
    """Base test class for the NICs tests.

    It comes with helper methods to create a mock cloudify context, with
    the specified relationships.
    """
    mock_neutron = MockNeutronClient()

    def _relationship_spec(self, obj, objtype):
        return {'node': {'properties': obj},
                'instance': {
                    'runtime_properties': {OPENSTACK_TYPE_PROPERTY: objtype,
                                           OPENSTACK_ID_PROPERTY: obj['id']}}}

    def _make_vm_ctx_with_ports(self, management_network_name, ports):
        port_specs = [self._relationship_spec(obj, PORT_OPENSTACK_TYPE)
                      for obj in ports]
        vm_properties = {'management_network_name': management_network_name}
        return self._make_vm_ctx_with_relationships(port_specs,
                                                    vm_properties)

    def _make_vm_ctx_with_networks(self, management_network_name, networks):
        network_specs = [self._relationship_spec(obj, NETWORK_OPENSTACK_TYPE)
                         for obj in networks]
        vm_properties = {'management_network_name': management_network_name}
        return self._make_vm_ctx_with_relationships(network_specs,
                                                    vm_properties)


class TestServerNICs(NICTestBase):
    """Test preparing the NICs list from server<->network relationships.

    Each test creates a cloudify context that represents a openstack VM
    with relationships to networks. Then, examine the NICs list produced from
    the relationships.
    """
    def test_nova_server_creation_nics_ordering(self):
        """NIC list keeps the order of the relationships.

        The nics= list passed to nova.server.create should be ordered
        depending on the relationships to the networks (as defined in the
        blueprint).
        """
        ctx = self._make_vm_ctx_with_networks(
            management_network_name='network1',
            networks=[
                {'id': '1'},
                {'id': '2'},
                {'id': '3'},
                {'id': '4'},
                {'id': '5'},
                {'id': '6'},
            ])
        server = {'meta': {}}

        _prepare_server_nics(
            self.mock_neutron, ctx, server)

        self.assertEqual(
            ['1', '2', '3', '4', '5', '6'],
            [n['net-id'] for n in server['nics']])

    def test_server_creation_prepends_mgmt_network(self):
        """If the management network isn't in a relation, it's the first NIC.

        Creating the server examines the relationships, and if it doesn't find
        a relationship to the management network, it adds the management
        network to the NICs list, as the first element.
        """
        ctx = self._make_vm_ctx_with_networks(
            management_network_name='other',
            networks=[
                {'id': '1'},
                {'id': '2'},
                {'id': '3'},
                {'id': '4'},
                {'id': '5'},
                {'id': '6'},
            ])
        server = {'meta': {}}

        _prepare_server_nics(
            self.mock_neutron, ctx, server)

        first_nic = server['nics'][0]
        self.assertEqual('other', first_nic['net-id'])
        self.assertEqual(7, len(server['nics']))

    def test_server_creation_uses_relation_mgmt_nic(self):
        """If the management network is in a relation, it isn't prepended.

        If the server has a relationship to the management network,
        a new NIC isn't prepended to the list.
        """
        ctx = self._make_vm_ctx_with_networks(
            management_network_name='network1',
            networks=[
                {'id': '1'},
                {'id': '2'},
                {'id': '3'},
                {'id': '4'},
                {'id': '5'},
                {'id': '6'},
            ])
        server = {'meta': {}}

        _prepare_server_nics(
            self.mock_neutron, ctx, server)
        self.assertEqual(6, len(server['nics']))


class TestServerPortNICs(NICTestBase):
    """Test preparing the NICs list from server<->port relationships.

    Create a cloudify ctx representing a vm with relationships to
    openstack ports. Then examine the resulting NICs list: check that it
    contains the networks that the ports were connected to, and that each
    connection uses the port that was provided.
    """

    def test_network_with_port(self):
        """Port on the management network is used to connect to it.

        The NICs list entry for the management network contains the
        port-id of the port from the relationship, but doesn't contain net-id.
        """
        ports = [{'id': '1'}]
        ctx = self._make_vm_ctx_with_ports('network1', ports)
        server = {'meta': {}}

        _prepare_server_nics(
            self.mock_neutron, ctx, server)

        self.assertEqual([{'port-id': '1'}], server['nics'])

    def test_port_not_to_mgmt_network(self):
        """A NICs list entry is added with the network and the port.

        A relationship to a port must not only add a NIC, but the NIC must
        also make sure to use that port.
        """
        ports = [{'id': '1'}]
        ctx = self._make_vm_ctx_with_ports('other', ports)
        server = {'meta': {}}

        _prepare_server_nics(
            self.mock_neutron, ctx, server)
        expected = [
            {'net-id': 'other'},
            {'port-id': '1'}
        ]
        self.assertEqual(expected, server['nics'])


class TestBootFromVolume(unittest.TestCase):

    @mock.patch('nova_plugin.server._get_boot_volume_relationships',
                autospec=True)
    def test_handle_boot_volume(self, mock_get_rels):
        mock_get_rels.return_value.runtime_properties = {
                'external_id': 'test-id',
                'availability_zone': 'test-az',
                }
        server = {}
        ctx = mock.MagicMock()
        nova_plugin.server._handle_boot_volume(server, ctx)
        self.assertEqual({'vda': 'test-id:::0'},
                         server['block_device_mapping'])
        self.assertEqual('test-az',
                         server['availability_zone'])

    @mock.patch('nova_plugin.server._get_boot_volume_relationships',
                autospec=True, return_value=[])
    def test_handle_boot_volume_no_boot_volume(self, *_):
        server = {}
        ctx = mock.MagicMock()
        nova_plugin.server._handle_boot_volume(server, ctx)
        self.assertNotIn('block_device_mapping', server)


class TestImageFromRelationships(unittest.TestCase):

    @mock.patch('glance_plugin.image.'
                'get_openstack_ids_of_connected_nodes_by_openstack_type',
                autospec=True, return_value=['test-id'])
    def test_handle_boot_image(self, *_):
        server = {}
        ctx = mock.MagicMock()
        nova_plugin.server.handle_image_from_relationship(server, 'image', ctx)
        self.assertEqual({'image': 'test-id'}, server)

    @mock.patch('glance_plugin.image.'
                'get_openstack_ids_of_connected_nodes_by_openstack_type',
                autospec=True, return_value=[])
    def test_handle_boot_image_no_image(self, *_):
        server = {}
        ctx = mock.MagicMock()
        nova_plugin.server.handle_image_from_relationship(server, 'image', ctx)
        self.assertNotIn('image', server)


@mock.patch('openstack_plugin_common.OpenStackClient._validate_auth_params')
class TestServerSGAttachments(unittest.TestCase):
    SecurityGroup = collections.namedtuple(
        'SecurityGroup', ['id', 'name'], verbose=True)

    def setUp(self):
        ctx = MockCloudifyContext(
            target=MockContext({
                'instance': MockNodeInstanceContext(
                    'sg1', {
                        OPENSTACK_ID_PROPERTY: 'test-sg',
                        OPENSTACK_NAME_PROPERTY: 'test-sg-name'
                    })
            }),
            source=MockContext({
                'node': mock.MagicMock(),
                'instance': MockNodeInstanceContext(
                    'server', {
                        OPENSTACK_ID_PROPERTY: 'server'
                    }
                )})
        )

        current_ctx.set(ctx)
        self.addCleanup(current_ctx.clear)
        findctx = mock.patch(
            'openstack_plugin_common._find_context_in_kw',
            return_value=ctx,
        )
        findctx.start()
        self.addCleanup(findctx.stop)

    @mock.patch('openstack_plugin_common.NovaClientWithSugar')
    def test_detach_already_detached(self, client, *kwargs):
        server = client.return_value.servers.get.return_value
        server.remove_security_group.side_effect = \
            nova_exceptions.NotFound('test')
        nova_plugin.server.disconnect_security_group()

    @mock.patch('openstack_plugin_common.NovaClientWithSugar')
    def test_connect_not_connected(self, client, *kwargs):
        security_groups = [self.SecurityGroup('test-sg-2', 'test-sg-2-name')]
        server = client.return_value.servers.get.return_value
        server.list_security_group.return_value = security_groups
        server.add_security_group.side_effect = (
            lambda _: security_groups.append(
                self.SecurityGroup('test-sg', 'test-sg-name')))
        nova_plugin.server.connect_security_group()
        server.add_security_group.assert_called_once_with('test-sg-name')

    @mock.patch('openstack_plugin_common.NovaClientWithSugar')
    def test_connect_already_connected(self, client, *kwargs):
        security_groups = [self.SecurityGroup('test-sg', 'test-sg-name'),
                           self.SecurityGroup('test-sg-2', 'test-sg-2-name')]
        server = client.return_value.servers.get.return_value
        server.list_security_group.return_value = security_groups
        nova_plugin.server.connect_security_group()
        server.add_security_group.assert_not_called()


class TestServerRelationships(unittest.TestCase):

    def _get_ctx_mock(self, instance_id, boot):
        rel_specs = [MockRelationshipContext(
            target=MockRelationshipSubjectContext(node=MockNodeContext(
                properties={'boot': boot}), instance=MockNodeInstanceContext(
                runtime_properties={
                    OPENSTACK_TYPE_PROPERTY: VOLUME_OPENSTACK_TYPE,
                    OPENSTACK_ID_PROPERTY: instance_id,
                    VOLUME_BOOTABLE: False
                })))]
        ctx = mock.MagicMock()
        ctx.instance = MockNodeInstanceContext(relationships=rel_specs)
        ctx.logger = setup_logger('mock-logger')
        return ctx

    def test_boot_volume_relationship(self):
        instance_id = 'test-id'
        ctx = self._get_ctx_mock(instance_id, True)
        rel_target = ctx.instance.relationships[0].target
        rel_target.instance.runtime_properties[VOLUME_BOOTABLE] = True
        result = nova_plugin.server._get_boot_volume_relationships(
            VOLUME_OPENSTACK_TYPE, ctx)
        self.assertEqual(
                instance_id,
                result.runtime_properties['external_id'])

    def test_no_boot_volume_relationship(self):
        instance_id = 'test-id'
        ctx = self._get_ctx_mock(instance_id, False)
        result = nova_plugin.server._get_boot_volume_relationships(
            VOLUME_OPENSTACK_TYPE, ctx)
        self.assertFalse(result)


class TestServerNetworkRuntimeProperties(unittest.TestCase):

    @property
    def mock_ctx(self):
        return MockCloudifyContext(
            node_id='test',
            deployment_id='test',
            properties={},
            operation={'retry_number': 0},
            provider_context={'resources': {}}
        )

    def test_server_networks_runtime_properties_empty_server(self):
        ctx = self.mock_ctx
        current_ctx.set(ctx=ctx)
        server = mock.MagicMock()
        setattr(server, 'networks', {})
        with self.assertRaisesRegexp(
                NonRecoverableError,
                'The server was created but not attached to a network.'):
            nova_plugin.server._set_network_and_ip_runtime_properties(server)

    def test_server_networks_runtime_properties_valid_networks(self):
        ctx = self.mock_ctx
        current_ctx.set(ctx=ctx)
        server = mock.MagicMock()
        network_id = 'management_network'
        network_ips = ['fd5f:5d21:845:1480:f816:3eff:fe23:817a',
                       '10.254.24.60', '10.254.24.61']
        setattr(server,
                'networks',
                {network_id: network_ips})
        nova_plugin.server._set_network_and_ip_runtime_properties(server)
        self.assertIn('networks', ctx.instance.runtime_properties.keys())
        self.assertIn('ip', ctx.instance.runtime_properties.keys())
        self.assertEquals(ctx.instance.runtime_properties['ip'],
                          '10.254.24.60')
        self.assertEquals(ctx.instance.runtime_properties['networks'],
                          {network_id: network_ips})
        self.assertIn('ipv4_address', ctx.instance.runtime_properties)
        self.assertIn('ipv4_addresses', ctx.instance.runtime_properties)
        self.assertIn('ipv6_address', ctx.instance.runtime_properties)
        self.assertIn('ipv6_addresses', ctx.instance.runtime_properties)

    def test_server_networks_runtime_properties_valid_networks_no_mgmt(self):
        ctx = self.mock_ctx
        current_ctx.set(ctx=ctx)
        server = mock.MagicMock()
        network_id = None
        network_ips = ['fd5f:5d21:845:1480:f816:3eff:fe23:817a',
                       '10.254.24.60', '10.254.24.61']
        setattr(server,
                'networks',
                {network_id: network_ips})
        nova_plugin.server._set_network_and_ip_runtime_properties(server)
        self.assertIn('networks', ctx.instance.runtime_properties.keys())
        self.assertIn('ip', ctx.instance.runtime_properties.keys())
        self.assertEquals(ctx.instance.runtime_properties['ip'],
                          '10.254.24.60')
        self.assertEquals(ctx.instance.runtime_properties['networks'],
                          {network_id: network_ips})

    def test_server_networks_runtime_properties_empty_networks(self):
        ctx = self.mock_ctx
        current_ctx.set(ctx=ctx)
        server = mock.MagicMock()
        network_id = 'management_network'
        network_ips = []
        setattr(server,
                'networks',
                {network_id: network_ips})
        nova_plugin.server._set_network_and_ip_runtime_properties(server)
        self.assertIn('networks', ctx.instance.runtime_properties.keys())
        self.assertIn('ip', ctx.instance.runtime_properties.keys())
        self.assertEquals(ctx.instance.runtime_properties['ip'], None)
        self.assertEquals(ctx.instance.runtime_properties['networks'],
                          {network_id: network_ips})
