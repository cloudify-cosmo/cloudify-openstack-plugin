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

import novaclient.v1_1.client as nova_client

from cloudify.mocks import MockCloudifyContext
import openstack_plugin_common as common
import openstack_plugin_common.tests.test as common_test

import nova_plugin.server


class ResourcesRenamingTest(unittest.TestCase):

    def setUp(self):
        # *** Configs from files ********************
        common.Config.get = mock.Mock()
        common.Config.get.return_value = {}
        # *** Nova ********************
        self.nova_mock = mock.Mock()
        # Next line was derived from
        # https://github.com/openstack/python-novaclient/blob/d05da4e985036fa354cc1f2666e39c4aa3213609/novaclient/v1_1/client.py#L103  # noqa
        self.nova_mock.servers = nova_client.servers.ServerManager(self)
        for a in 'servers_proxy', 'images_proxy', 'flavors_proxy':
            proxy = getattr(self.nova_mock, a)
            ls = getattr(proxy, 'list')
            ls.return_value = []

        def nova_mock_connect(unused_self, unused_cfg, unused_region=None):
            return self.nova_mock
        common.NovaClient.connect = nova_mock_connect

        # Don't let override our mock proxies.
        # They are already set up when add_proxies_to_nova_client()
        # is called.
        common.add_proxies_to_nova_client = mock.Mock()

        # *** Neutron ********************
        self.neutron_mock = mock.Mock()
        self.neutron_mock.cosmo_get_named.return_value = {'id': 'MOCK_MGR_NET'}

        def neutron_mock_connect(unused_self, unused_cfg):
            return self.neutron_mock
        common.NeutronClient.connect = neutron_mock_connect

    def test_resources_renaming(self):
        ctx = MockCloudifyContext(
            node_id='__cloudify_id_server_001',
            properties={
                'server': {
                    'name': 'server_name',
                    'image': 'DUMMY_IMAGE',
                    'flavor': 'DUMMY_FLAVOR',
                    'key_name': 'key_name',
                },
                'management_network_name': 'mg_net_name',
            }
        )

        common_test.set_mock_provider_context_from_file(ctx)
        nova_plugin.server.start(ctx)
        calls = self.nova_mock.servers_proxy.create.mock_calls
        self.assertEquals(len(calls), 1)  # Exactly one server created
        kw = calls[0][2]  # 2 - kwargs, which in case of Nova are all args
        self.assertEquals(kw['name'], 'p2_server_name')
        self.assertEquals(kw['key_name'], 'p2_key_name')
        self.assertEquals(
            kw.get('meta', {})['cloudify_management_network_name'],
            'p2_mg_net_name'
        )
        self.assertEquals(kw['security_groups'], ['p2_cloudify-sg-agents'])

if __name__ == '__main__':
    unittest.main()
