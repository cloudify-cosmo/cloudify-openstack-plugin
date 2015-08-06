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

from os import path
import tempfile

import unittest
import mock

import nova_plugin
from cloudify.test_utils import workflow_test


class TestServer(unittest.TestCase):

    blueprint_path = path.join('resources',
                               'test-start-operation-retry-blueprint.yaml')

    @mock.patch('nova_plugin.server.create')
    @mock.patch('nova_plugin.server._set_network_and_ip_runtime_properties')
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
    def test_nova_server_creation_param_integrity(self, cfy_local, *args):
        class MyDict(dict):
            id = 'uid'

        def mock_create_server(*args, **kwargs):
            key_args = MyDict(kwargs)
            self.assertIn('scheduler_hints', key_args)
            self.assertEqual(key_args['scheduler_hints'],
                             {'group': 'affinity-group-id'},
                             'expecting \'scheduler_hints\' value to exist')
            return key_args

        with mock.patch('openstack_plugin_common.nova_client.servers.'
                        'ServerManager.create', new=mock_create_server):
            cfy_local.execute('install', task_retries=0)

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

        tmp_path = tempfile.NamedTemporaryFile(prefix='key_name')
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
