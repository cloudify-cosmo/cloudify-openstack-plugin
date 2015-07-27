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
from functools import wraps

import nova_plugin


IGNORED_LOCAL_WORKFLOW_MODULES = (
    'worker_installer.tasks',
    'plugin_installer.tasks',
    'cloudify_agent.operations',
    'cloudify_agent.installer.operations',
)


class set_testing_env(object):
    def __init__(self, **kwargs):
        # Set custom setUp and teardown (if exists)
        if 'setUp' in kwargs:
            self.setUp = kwargs.get('setUp')
        if 'tearDown' in kwargs:
            self.tearDown = kwargs.get('tearDown')

        # blueprint to run
        self.blueprint_filename = kwargs.get('blueprint_filename')
        self.blueprint_path = path.join(path.dirname(__file__),
                                        'resources',
                                        self.blueprint_filename)
        # Plugin path and name
        plugin_yaml_path = kwargs.get('plugin_yaml_path')
        if plugin_yaml_path:
            self.plugin_yaml_filename = path.basename(plugin_yaml_path)
            self.plugin_yaml_path = path.dirname(plugin_yaml_path)
        else:
            self.plugin_yaml_filename = 'plugin.yaml'
            self.plugin_yaml_path = path.abspath(
                path.join(path.dirname(nova_plugin.__file__),
                          '../plugin.yaml'))

        # Set prefix for resources
        self.prefix = kwargs['prefix'] if 'prefix' in kwargs \
            else "{}-unit-tests-".format(__name__[:__name__.index('.')])

        # Setting inputs file
        self.inputs = kwargs.get('inputs')

    def setUp(self, test_method_name):
        class test_env:
            def __init__(self):
                pass

        test_env.counter = 0
        test_env.server = mock.MagicMock()
        tempdir = tempfile.mkdtemp(self.prefix)

        temp_blueprint_path = path.join(tempdir, self.blueprint_filename)
        temp_plugin_yaml_path = path.join(tempdir, self.plugin_yaml_filename)

        shutil.copyfile(self.blueprint_path, temp_blueprint_path)
        shutil.copyfile(self.plugin_yaml_path, temp_plugin_yaml_path)

        # setup local workflow execution environment
        test_env.env = local.init_env(
            temp_blueprint_path,
            name=test_method_name,
            ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES,
            inputs=self.inputs)

        return test_env, tempdir

    def tearDown(self, tempdir):
        if path.exists(tempdir):
            shutil.rmtree(tempdir)

    def __call__(self, test):
        @wraps(test)
        def wrapped_test(func, *args, **kwargs):
            test_env, tempdir = self.setUp(func._testMethodName)
            test(func, test_env, *args, **kwargs)
            self.tearDown(tempdir)

        return wrapped_test


class TestServer(unittest.TestCase):
    @set_testing_env(
        blueprint_filename='test-start-operation-retry-blueprint.yaml')
    @mock.patch('nova_plugin.server.create')
    @mock.patch('nova_plugin.server._set_network_and_ip_runtime_properties')
    def test_nova_server_lifecycle_start(self, test_env, *_):
        def mock_get_server_by_context(*_):
            s = test_env.server
            if test_env.counter == 0:
                s.status = nova_plugin.server.SERVER_STATUS_BUILD
            else:
                s.status = nova_plugin.server.SERVER_STATUS_ACTIVE
            test_env.counter += 1
            return s

        with mock.patch('nova_plugin.server.get_server_by_context',
                        new=mock_get_server_by_context):
            test_env.env.execute('install', task_retries=3)

        self.assertEqual(2, test_env.counter)
        self.assertEqual(0, test_env.server.start.call_count)

    @set_testing_env(
        blueprint_filename='test-start-operation-retry-blueprint.yaml')
    @mock.patch('nova_plugin.server.create')
    @mock.patch('nova_plugin.server._set_network_and_ip_runtime_properties')
    def test_nova_server_lifecycle_start_after_stop(self, test_env, *_):
        def mock_get_server_by_context(_):
            s = test_env.server
            if test_env.counter == 0:
                s.status = nova_plugin.server.SERVER_STATUS_SHUTOFF
            elif test_env.counter == 1:
                setattr(s,
                        nova_plugin.server.OS_EXT_STS_TASK_STATE,
                        nova_plugin.server.SERVER_TASK_STATE_POWERING_ON)
            else:
                s.status = nova_plugin.server.SERVER_STATUS_ACTIVE
            test_env.counter += 1
            test_env.server = s
            return s

        with mock.patch('nova_plugin.server.get_server_by_context',
                        new=mock_get_server_by_context):
            test_env.env.execute('install', task_retries=3)

        self.assertEqual(1, test_env.server.start.call_count)
        self.assertEqual(3, test_env.counter)

    @set_testing_env(
        blueprint_filename='test-start-operation-retry-blueprint.yaml')
    @mock.patch('nova_plugin.server.create')
    @mock.patch('nova_plugin.server._set_network_and_ip_runtime_properties')
    def test_nova_server_lifecycle_start_unknown_status(self, test_env, *_):
        def mock_get_server_by_context(_):
            s = test_env.server
            if test_env.counter == 0:
                s.status = '### unknown-status ###'
            test_env.counter += 1
            test_env.server = s
            return s

        with mock.patch('nova_plugin.server.get_server_by_context',
                        new=mock_get_server_by_context):
            self.assertRaisesRegexp(RuntimeError,
                                    'Unexpected server state',
                                    test_env.env.execute,
                                    'install')

        self.assertEqual(0, test_env.server.start.call_count)
        self.assertEqual(1, test_env.counter)

    @set_testing_env(
        blueprint_filename='test-start-operation-retry-blueprint.yaml')
    @mock.patch('nova_plugin.server.start')
    @mock.patch('nova_plugin.server._handle_image_or_flavor')
    @mock.patch('nova_plugin.server._fail_on_missing_required_parameters')
    def test_nova_server_creation_param_integrity(self, test_env, *_):
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
            test_env.env.execute('install', task_retries=0)

    @set_testing_env(
        blueprint_filename='test-start-operation-retry-blueprint.yaml',
        inputs={'use_password': True})
    @mock.patch('nova_plugin.server.create')
    @mock.patch('nova_plugin.server._set_network_and_ip_runtime_properties')
    @mock.patch(
        'nova_plugin.server.get_single_connected_node_by_openstack_type',
        autospec=True, return_value=None)
    @mock.patch('os.path.isfile', autospec=True, return_value=True)
    def test_nova_server_with_use_password(self, test_env, *_):

        key_path = 'some_private_key_path'

        def mock_get_server_by_context(_):
            s = test_env.server
            if test_env.counter == 0:
                s.status = nova_plugin.server.SERVER_STATUS_BUILD
            else:
                s.status = nova_plugin.server.SERVER_STATUS_ACTIVE
            test_env.counter += 1

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
                test_env.env.execute('install', task_retries=5)
