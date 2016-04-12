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

from nova_plugin.server import _merge_nics
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


@mock.patch('nova_plugin.server.start')
@mock.patch('nova_plugin.server._handle_image_or_flavor')
@mock.patch('nova_plugin.server._fail_on_missing_required_parameters')
class TestServerNICs(unittest.TestCase):
    blueprint_path = path.join('resources',
                               'test-networks-relationships-blueprint.yaml')

    @staticmethod
    def mock_get_networks(neutron, name=None, **search_params):
        networks = [
            {'name': 'network1', 'id': '1'},
            {'name': 'network2', 'id': '2'},
            {'name': 'network3', 'id': '3'},
            {'name': 'network4', 'id': '4'},
            {'name': 'network5', 'id': '5'},
            {'name': 'network6', 'id': '6'},
            {'name': 'other', 'id': 'other'}
        ]
        # this method is used to both list all networks, and to search
        # for networks by name - the mock needs to implement both cases
        if name is not None:
            return {'networks': [n for n in networks if n['name'] == name]}
        return {'networks': networks}

    @staticmethod
    def mock_get_ports(neutron, name=None, **search_params):
        ports = [
            {'name': 'port1', 'id': 'port1'},
        ]
        # this method is used to both list all networks, and to search
        # for networks by name - the mock needs to implement both cases
        if name is not None:
            return {'ports': [n for n in ports if n['name'] == name]}
        return {'ports': ports}

    def test_merge_prepends_management_network(self, *mocks):
        """When the mgmt network isnt in a relationship, its the 1st nic."""
        mgmt_network_id = 'management network'
        nics = [{'net-id': 'other network'}]

        merged = _merge_nics(mgmt_network_id, nics)

        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0]['net-id'], 'management network')

    def test_management_network_in_relationships(self, *mocks):
        """When the mgmt network was in a relationship, it's not prepended."""
        mgmt_network_id = 'management network'
        nics = [{'net-id': 'other network'}, {'net-id': 'management network'}]

        merged = _merge_nics(mgmt_network_id, nics)

        self.assertEqual(nics, merged)

    @workflow_test(blueprint_path, copy_plugin_yaml=True)
    def test_nova_server_creation_nics_ordering(self, cfy_local, *mocks):
        """NIC list keeps the order of the relationships from the blueprint.

        The nics= list passed to nova.server.create should be ordered
        depending on the relationships to the networks, as defined in the
        blueprint.
        This test unfortunately necessarily depends on dict ordering to fail:
        it's still possible for the NICs to be correctly ordered by chance,
        although with 6 elements, the chance is negligible.
        """
        with mock.patch('openstack_plugin_common.nova_client.servers.'
                        'ServerManager.create') as mock_create, \
            mock.patch('openstack_plugin_common.neutron_client.Client.'
                       'list_networks', new=self.mock_get_networks), \
            mock.patch('openstack_plugin_common.neutron_client.Client.'
                       'list_ports', new=self.mock_get_ports):

            cfy_local.execute('install', task_retries=0)

        self.assertEqual(1, len(mock_create.mock_calls))
        server_args, server_kwargs = mock_create.call_args_list[0]

        network_ids = [n['net-id'] for n in server_kwargs['nics']]
        self.assertEqual(['1', '2', '3', '4', '5', '6'], network_ids)

    @workflow_test(blueprint_path, copy_plugin_yaml=True, inputs={
        'management_network_name': 'other'
    })
    def test_server_creation_prepends_mgmt_network(self, cfy_local, *mocks):
        """When the mgmt network isnt in a relationship, its the 1st nic.

        Creating the server examines the relationships, and if it doesn't find
        a relationship to the management network, id adds the network to the
        NICs list anyway, as the first element.
        """
        with mock.patch('openstack_plugin_common.nova_client.servers.'
                        'ServerManager.create') as mock_create, \
            mock.patch('openstack_plugin_common.neutron_client.Client.'
                       'list_networks', new=self.mock_get_networks):

            cfy_local.execute('install', task_retries=0)

        self.assertEqual(len(mock_create.mock_calls), 1)
        server_args, server_kwargs = mock_create.call_args_list[0]

        first_nic = server_kwargs['nics'][0]
        self.assertEqual('other', first_nic['net-id'])

    @workflow_test(blueprint_path, copy_plugin_yaml=True, inputs={
        'management_network_name': 'network1'
    })
    def test_server_creation_uses_relation_mgmt_nic(self, cfy_local, *mocks):
        """When the mgmt network is in a relationship, it isn't prepended.

        If the server has a relationship to the management network,
        a new NIC isn't prepended to the list.
        """
        with mock.patch('openstack_plugin_common.nova_client.servers.'
                        'ServerManager.create') as mock_create, \
            mock.patch('openstack_plugin_common.neutron_client.Client.'
                       'list_networks', new=self.mock_get_networks):

            cfy_local.execute('install', task_retries=0)

        self.assertEqual(1, len(mock_create.mock_calls))
        server_args, server_kwargs = mock_create.call_args_list[0]

        # blueprint defines 6 network relationships, so there should be 6 NICs,
        # not 7
        self.assertEqual(6, len(server_kwargs['nics']))
