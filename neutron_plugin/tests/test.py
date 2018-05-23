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
import random
import string
import unittest

from cloudify.context import BootstrapContext
from cloudify.state import current_ctx

from cloudify.mocks import MockCloudifyContext

import openstack_plugin_common
import openstack_plugin_common.tests.test as common_test

import neutron_plugin
import neutron_plugin.network
import neutron_plugin.port
import neutron_plugin.router
import neutron_plugin.security_group


@mock.patch('openstack_plugin_common.NeutronClientWithSugar')
class ResourcesRenamingTest(unittest.TestCase):

    def setUp(self):
        config_get = mock.patch(
            'openstack_plugin_common.Config.get',
            mock.Mock(return_value={}),
        )
        config_get.start()
        self.addCleanup(config_get.stop)

    def _setup_ctx(self, obj_type):
        self.ctx = common_test.create_mock_ctx_with_provider_info(
            node_id='__cloudify_id_something_001',
            properties={
                'resource_id': 'resource_id',
                'description': 'description',
                'external_network': 'external_network',
                obj_type: {
                    'name': obj_type + '_name',
                },
                'rules': []  # For security_group
            }
        )
        current_ctx.set(self.ctx)
        self.addCleanup(current_ctx.clear)
        return self.ctx

    def _test(self, obj_type, neutron_mock, additional={}):
        neutron_mock.cosmo_list = mock.Mock()
        neutron_mock.cosmo_list.return_value = []
        attr = getattr(neutron_mock, 'create_' + obj_type)

        obj_return = {
            'id': obj_type + '_id',
            'name': obj_type + '_name'
        }
        obj_return.update(additional)

        attr.return_value = {
            obj_type: obj_return
        }
        with mock.patch('openstack_plugin_common._find_context_in_kw',
                        return_value=self.ctx):
            getattr(neutron_plugin, obj_type).create(
                neutron_client=neutron_mock,
                ctx=self.ctx, args={})

        calls = attr.mock_calls
        self.assertEquals(len(calls), 1)  # Exactly one object created
        # Indexes into call[]:
        # 0 - the only call
        # 1 - regular arguments
        # 0 - first argument
        arg = calls[0][1][0]
        self.assertEquals(arg[obj_type]['name'], 'p2_' + obj_type + '_name')

    def test_network(self, neutron_mock):
        self._setup_ctx('network')
        self._test('network', neutron_mock)

    def test_port(self, neutron_mock):
        self._setup_ctx('port')
        self.ctx.node.properties['fixed_ip'] = "1.2.3.4"
        fake_instance = mock.Mock()
        fake_instance.target.instance.runtime_properties = {
            openstack_plugin_common.OPENSTACK_TYPE_PROPERTY: 'network',
            openstack_plugin_common.OPENSTACK_ID_PROPERTY: 'network_id'
        }
        self.ctx._instance._relationships = [
            fake_instance
        ]
        self._test('port', neutron_mock, {'fixed_ips': None,
                                          'mac_address': 'mac_address'})

    def test_router(self, neutron_mock):
        self._setup_ctx('router')
        self._test('router', neutron_mock)

    def test_security_group(self, neutron_mock):
        self._setup_ctx('security_group')
        self._test('security_group', neutron_mock, )

    # Network chosen arbitrary for this test.
    # Just testing something without prefix.
    def test_network_no_prefix(self, neutron_mock):
        ctx = self._setup_ctx('network')
        for pctx in common_test.BOOTSTRAP_CONTEXTS_WITHOUT_PREFIX:
            ctx._bootstrap_context = BootstrapContext(pctx)
            neutron_mock.create_network.reset_mock()
            neutron_mock.create_network.return_value = {
                'network': {
                    'id': 'network_id',
                    'name': 'network_name',
                }
            }

            with mock.patch('openstack_plugin_common._find_context_in_kw',
                            return_value=self.ctx):
                neutron_plugin.network.create(neutron_client=neutron_mock,
                                              ctx=self.ctx, args={})

            neutron_mock.create_network.assert_called_once_with({
                'network': {'name': 'network_name', 'admin_state_up': True}
            })


def _rand_str(n):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(n))


@mock.patch('openstack_plugin_common.NeutronClientWithSugar')
class SecurityGroupTest(unittest.TestCase):

    def setUp(self):
        # *** Configs from files ********************
        config_get = mock.patch(
            'openstack_plugin_common.Config.get',
            mock.Mock(return_value={}),
        )
        config_get.start()
        self.addCleanup(config_get.stop)

        # context
        sg_name = _rand_str(6) + '_new'
        self.ctx = MockCloudifyContext(
            node_id='test',
            deployment_id='test',
            properties={
                'description': 'The best Security Group. Great',
                'resource_id': 'mock_sg',
                'security_group': {
                    'name': sg_name,
                    'description': 'blah'
                },
                'rules': [{'port': 80}],
                'disable_default_egress_rules': True,
            }
        )
        current_ctx.set(self.ctx)
        self.addCleanup(current_ctx.clear)

    def test_sg_new(self, neutron_mock):
        neutron_plugin.security_group._rules_for_sg_id = mock.Mock()
        neutron_plugin.security_group._rules_for_sg_id.return_value = []

        neutron_mock.cosmo_list = mock.Mock()
        neutron_mock.cosmo_list.return_value = []
        neutron_mock.create_security_group = mock.Mock()
        neutron_mock.create_security_group.return_value = {
            'security_group': {
                'description': 'blah',
                'id': self.ctx._properties['security_group']['name'] + '_id',
            }
        }

        with mock.patch('openstack_plugin_common._find_context_in_kw',
                        return_value=self.ctx):
            neutron_plugin.security_group.create(neutron_client=neutron_mock,
                                                 ctx=self.ctx, args={})

        neutron_mock.create_security_group.assert_called_once_with({
            'security_group': {
                'description': 'blah',
                'name': self.ctx._properties['security_group']['name']
            }
        })

    def test_sg_use_existing(self, neutron_mock):
        neutron_plugin.security_group._rules_for_sg_id = mock.Mock()
        neutron_plugin.security_group._rules_for_sg_id.return_value = []

        neutron_mock.cosmo_list = mock.Mock()
        neutron_mock.cosmo_list.return_value = [{
            'id': self.ctx._properties['security_group']['name'] + '_ex_id',
            'description': 'blah',
            'security_group_rules': [{
                'remote_group_id': None,
                'direction': 'ingress',
                'protocol': 'tcp',
                'ethertype': 'IPv4',
                'port_range_max': 80,
                'port_range_min': 80,
                'remote_ip_prefix': '0.0.0.0/0',
            }]
        }]
        neutron_mock.create_security_group = mock.Mock()
        neutron_mock.create_security_group.return_value = {
            'security_group': {
                'description': 'blah',
                'id': self.ctx._properties['security_group']['name'] + '_id',
            }
        }

        with mock.patch('openstack_plugin_common._find_context_in_kw',
                        return_value=self.ctx):
            neutron_plugin.security_group.create(neutron_client=neutron_mock,
                                                 ctx=self.ctx, args={})

        neutron_mock.create_security_group.assert_called_once_with({
            'security_group': {
                'description': 'blah',
                'name': self.ctx._properties['security_group']['name']
            }
        })

    def test_sg_use_existing_with_other_rules(self, neutron_mock):
        neutron_plugin.security_group._rules_for_sg_id = mock.Mock()
        neutron_plugin.security_group._rules_for_sg_id.return_value = []

        neutron_mock.cosmo_list = mock.Mock()
        neutron_mock.cosmo_list.return_value = [{
            'id': self.ctx._properties['security_group']['name'] + '_ex_id',
            'description': 'blah',
            'security_group_rules': [{
                'remote_group_id': None,
                'direction': 'ingress',
                'protocol': 'tcp',
                'ethertype': 'IPv4',
                'port_range_max': 81,  # Note the different port!
                'port_range_min': 81,  # Note the different port!
                'remote_ip_prefix': '0.0.0.0/0',
            }]
        }]
        neutron_mock.create_security_group = mock.Mock()
        neutron_mock.create_security_group.return_value = {
            'security_group': {
                'description': 'blah',
                'id': self.ctx._properties['security_group']['name'] + '_id',
            }
        }
        neutron_plugin.security_group.create(neutron_client=neutron_mock,
                                             ctx=self.ctx, args={})


if __name__ == '__main__':
    unittest.main()
