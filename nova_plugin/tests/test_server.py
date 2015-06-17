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


import shutil
import tempfile
import unittest
from os import path

import mock

from cloudify.workflows import local

import nova_plugin


IGNORED_LOCAL_WORKFLOW_MODULES = (
    'worker_installer.tasks',
    'plugin_installer.tasks'
)


class TestServer(unittest.TestCase):

    def setUp(self):
        self.counter = 0
        self.server = mock.MagicMock()
        blueprint_filename = 'test-start-operation-retry-blueprint.yaml'
        blueprint_path = path.join(path.dirname(__file__),
                                   'resources',
                                   blueprint_filename)
        plugin_yaml_filename = 'plugin.yaml'

        plugin_yaml_path = path.realpath(
            path.join(path.dirname(nova_plugin.__file__),
                      '../{0}'.format(plugin_yaml_filename)))

        self.tempdir = tempfile.mkdtemp(prefix='openstack-plugin-unit-tests-')

        temp_blueprint_path = path.join(self.tempdir, blueprint_filename)
        temp_plugin_yaml_path = path.join(self.tempdir, plugin_yaml_filename)

        shutil.copyfile(blueprint_path, temp_blueprint_path)
        shutil.copyfile(plugin_yaml_path, temp_plugin_yaml_path)

        # setup local workflow execution environment
        self.env = local.init_env(
            temp_blueprint_path,
            name=self._testMethodName,
            ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES)

    def tearDown(self):
        if path.exists(self.tempdir):
            shutil.rmtree(self.tempdir)

    @mock.patch('nova_plugin.server.create')
    @mock.patch('nova_plugin.server._set_network_and_ip_runtime_properties')
    def test_nova_server_lifecycle_start(self, *_):
        def mock_get_server_by_context(_):
            s = self.server
            if self.counter == 0:
                s.status = nova_plugin.server.SERVER_STATUS_BUILD
            else:
                s.status = nova_plugin.server.SERVER_STATUS_ACTIVE
            self.counter += 1
            return s

        with mock.patch('nova_plugin.server.get_server_by_context',
                        new=mock_get_server_by_context):
            self.env.execute('install', task_retries=3)

        self.assertEqual(2, self.counter)
        self.assertEqual(0, self.server.start.call_count)

    @mock.patch('nova_plugin.server.create')
    @mock.patch('nova_plugin.server._set_network_and_ip_runtime_properties')
    def test_nova_server_lifecycle_start_after_stop(self, *_):
        def mock_get_server_by_context(_):
            s = self.server
            if self.counter == 0:
                s.status = nova_plugin.server.SERVER_STATUS_SHUTOFF
            elif self.counter == 1:
                setattr(s,
                        nova_plugin.server.OS_EXT_STS_TASK_STATE,
                        nova_plugin.server.SERVER_TASK_STATE_POWERING_ON)
            else:
                s.status = nova_plugin.server.SERVER_STATUS_ACTIVE
            self.counter += 1
            self.server = s
            return s

        with mock.patch('nova_plugin.server.get_server_by_context',
                        new=mock_get_server_by_context):
            self.env.execute('install', task_retries=3)

        self.assertEqual(1, self.server.start.call_count)
        self.assertEqual(3, self.counter)

    @mock.patch('nova_plugin.server.create')
    @mock.patch('nova_plugin.server._set_network_and_ip_runtime_properties')
    def test_nova_server_lifecycle_start_unknown_status(self, *_):
        def mock_get_server_by_context(_):
            s = self.server
            if self.counter == 0:
                s.status = '### unknown-status ###'
            self.counter += 1
            self.server = s
            return s

        with mock.patch('nova_plugin.server.get_server_by_context',
                        new=mock_get_server_by_context):
            self.assertRaisesRegexp(RuntimeError,
                                    'Unexpected server state',
                                    self.env.execute,
                                    'install')

        self.assertEqual(0, self.server.start.call_count)
        self.assertEqual(1, self.counter)

    @mock.patch('nova_plugin.server.start')
    @mock.patch('nova_plugin.server._handle_image_or_flavor')
    @mock.patch('nova_plugin.server._fail_on_missing_required_parameters')
    def test_nova_server_creation_param_integrity(self, *_):
        class MyDict(dict):
            id = 'uid'

        def mock_create_server(*args, **kwargs):
            key_args = MyDict(kwargs)
            self.assertTrue('scheduler_hints' in key_args)
            self.assertEqual(key_args['scheduler_hints'],
                             {'group': 'affinity-group-id'},
                             'expecting \'scheduler_hints\' value to exist')
            return key_args

        with mock.patch('openstack_plugin_common.nova_client.servers.'
                        'ServerManager.create', new=mock_create_server):
            self.env.execute('install', task_retries=0)
