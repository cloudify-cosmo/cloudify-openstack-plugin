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

import mock
import unittest
import heat_plugin.stack

from cloudify.mocks import MockCloudifyContext
from cloudify.exceptions import NonRecoverableError


def ctx_mock(prop_dict):
    ctx = MockCloudifyContext(
        node_id='d',
        properties=prop_dict)
    ctx.download_resource = mock.MagicMock(return_value="path")
    return ctx


class TestStack(unittest.TestCase):
    @mock.patch('heat_plugin.stack.ctx',
                ctx_mock({"stack": {}}))
    @mock.patch('heat_plugin.stack.open', mock.MagicMock())
    def test_stack_create_with_empty_template(self):
        c_mock = ctx_mock({"stack": {}})
        with mock.patch('openstack_plugin_common.HeatClientWithSugar'):
            with self.assertRaises(NonRecoverableError):
                heat_plugin.stack.create(ctx=c_mock, args={})

    @mock.patch('heat_plugin.stack.ctx',
                ctx_mock({"stack": {}, "template_file": "file"}))
    @mock.patch('heat_plugin.stack.open', mock.MagicMock())
    @mock.patch('heat_plugin.stack._check_status', mock.MagicMock())
    def test_stack_create_with_template(self):
        c_mock = ctx_mock({"stack": {}, "template_file": "file"})
        with mock.patch('openstack_plugin_common.HeatClientWithSugar'):
            heat_plugin.stack.create(ctx=c_mock, args={})

    def test_stack_create_retry(self):
        c_mock = ctx_mock({"stack": {}})
        with mock.patch('openstack_plugin_common.HeatClientWithSugar') as c:
            with mock.patch('heat_plugin.stack.ctx', ctx_mock({})) as m:
                    m.instance.runtime_properties['stack_id'] = 1
                    c.return_value.stacks.get.return_value.stack_status =\
                        "CREATE_COMPLETE"
                    heat_plugin.stack.create(ctx=c_mock, args={})

    @mock.patch('heat_plugin.stack.ctx',
                ctx_mock({"stack": {}}))
    def test_stack_delete_empty_stack_id(self):
        c_mock = ctx_mock({"stack": {}})
        with mock.patch('openstack_plugin_common.HeatClientWithSugar'):
            with self.assertRaises(NonRecoverableError):
                heat_plugin.stack.delete(ctx=c_mock)

    def test_stack_delete_with_stack_id(self):
        c_mock = ctx_mock({"stack": {}})
        with mock.patch('openstack_plugin_common.HeatClientWithSugar'):
            with mock.patch('heat_plugin.stack.ctx', ctx_mock({})) as m:
                m.instance.runtime_properties['stack_id'] = 1
                heat_plugin.stack.delete(ctx=c_mock)

    @mock.patch('heat_plugin.stack.ctx',
                ctx_mock({"stack": {}}))
    def test_stack_start_empty_stack_id(self):
        c_mock = ctx_mock({"stack": {}})
        with mock.patch('openstack_plugin_common.HeatClientWithSugar'):
            with self.assertRaises(NonRecoverableError):
                heat_plugin.stack.start(ctx=c_mock)

    @mock.patch('heat_plugin.stack._check_status', mock.MagicMock())
    def test_stack_start_with_stack_id(self):
        c_mock = ctx_mock({"stack": {}})
        with mock.patch('openstack_plugin_common.HeatClientWithSugar'):
            with mock.patch('heat_plugin.stack.ctx', ctx_mock({})) as m:
                m.instance.runtime_properties['stack_id'] = 1
                heat_plugin.stack.start(ctx=c_mock)

    def test_check_status(self):
        stats = mock.MagicMock()
        stats.stacks.get.return_value.stack_status = "CREATE_COMPLETE"
        heat_plugin.stack._check_status(stats, None)

        with self.assertRaises(NonRecoverableError):
            stats.stacks.get.return_value.stack_status = "CREATE_FAILED"
            heat_plugin.stack._check_status(stats, None)

        with mock.patch('heat_plugin.stack.ctx', ctx_mock({})):
            stats.stacks.get.return_value.stack_status = "CREATE_IN_PROGRESS"
            heat_plugin.stack._check_status(stats, None)

        with self.assertRaises(NonRecoverableError):
            stats.stacks.get.return_value.stack_status = "UNKNOWN"
            heat_plugin.stack._check_status(stats, None)
