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

from cloudify.mocks import MockCloudifyContext
import openstack_plugin_common as common
import openstack_plugin_common.tests.test as common_test

import neutron_plugin
import neutron_plugin.network
import neutron_plugin.port
import neutron_plugin.router
import neutron_plugin.security_group


class ResourcesRenamingTest(unittest.TestCase):
    def setUp(self):
        neutron_plugin.port._find_network_in_related_nodes = mock.Mock()
        # *** Neutron ********************
        self.neutron_mock = mock.Mock()

        def neutron_mock_connect(unused_self, unused_cfg):
            return self.neutron_mock
        common.NeutronClient.connect = neutron_mock_connect

    def _test(self, obj_type):
        ctx = MockCloudifyContext(
            node_id='__cloudify_id_something_001',
            properties={
                obj_type: {
                    'name': obj_type + '_name',
                },
                'rules': []  # For security_group
            }
        )
        common_test.set_mock_provider_context_from_file(ctx)
        attr = getattr(self.neutron_mock, 'create_' + obj_type)
        attr.return_value = {
            obj_type: {
                'id': obj_type + '_id',
            }
        }
        getattr(neutron_plugin, obj_type).create(ctx)
        calls = attr.mock_calls
        self.assertEquals(len(calls), 1)  # Exactly one server created
        # Indexes into call[]:
        # 0 - the only call
        # 1 - regular arguments
        # 0 - first argument
        arg = calls[0][1][0]  # 1 - args, which in case of Nova are all args
        self.assertEquals(arg[obj_type]['name'], 'p2_' + obj_type + '_name')

    def test_network(self):
        self._test('network')

    def test_port(self):
        self._test('port')

    def test_router(self):
        self._test('router')

    def test_security_group(self):
        self._test('security_group')


if __name__ == '__main__':
    unittest.main()
