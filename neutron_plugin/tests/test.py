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

from cloudify.context import BootstrapContext

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
        # *** Configs from files ********************
        common.Config.get = mock.Mock()
        common.Config.get.return_value = {}
        # *** Neutron ********************
        self.neutron_mock = mock.Mock()

        def neutron_mock_connect(unused_self, unused_cfg):
            return self.neutron_mock
        common.NeutronClient.connect = neutron_mock_connect

    def _setup_ctx(self, obj_type):
        ctx = common_test.create_mock_ctx_with_provider_info(
            node_id='__cloudify_id_something_001',
            properties={
                obj_type: {
                    'name': obj_type + '_name',
                },
                'rules': []  # For security_group
            }
        )
        return ctx

    def _test(self, obj_type):
        ctx = self._setup_ctx(obj_type)
        attr = getattr(self.neutron_mock, 'create_' + obj_type)
        attr.return_value = {
            obj_type: {
                'id': obj_type + '_id',
            }
        }
        getattr(neutron_plugin, obj_type).create(ctx)
        calls = attr.mock_calls
        self.assertEquals(len(calls), 1)  # Exactly one object created
        # Indexes into call[]:
        # 0 - the only call
        # 1 - regular arguments
        # 0 - first argument
        arg = calls[0][1][0]
        self.assertEquals(arg[obj_type]['name'], 'p2_' + obj_type + '_name')

    def test_network(self):
        self._test('network')

    def test_port(self):
        self._test('port')

    def test_router(self):
        self._test('router')

    def test_security_group(self):
        self._test('security_group')

    # Network chosen arbitrary for this test.
    # Just testing something without prefix.
    def test_network_no_prefix(self):
        ctx = self._setup_ctx('network')
        for pctx in common_test.BOOTSTRAP_CONTEXTS_WITHOUT_PREFIX:
            ctx._bootstrap_context = BootstrapContext(pctx)
            self.neutron_mock.create_network.reset_mock()
            self.neutron_mock.create_network.return_value = {
                'network': {
                    'id': 'network_id',
                }
            }
            neutron_plugin.network.create(ctx)
            calls = self.neutron_mock.create_network.mock_calls
            self.assertEquals(len(calls), 1)  # Exactly one network created
            # Indexes into call[]:
            # 0 - the only call
            # 1 - regular arguments
            # 0 - first argument
            arg = calls[0][1][0]
            self.assertEquals(arg['network']['name'], 'network_name',
                              "Failed with context: " + str(pctx))


if __name__ == '__main__':
    unittest.main()
