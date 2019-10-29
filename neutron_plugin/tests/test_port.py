########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import unittest
import mock

import neutron_plugin.port
from neutron_plugin.security_group import SG_OPENSTACK_TYPE
from cloudify.mocks import (MockCloudifyContext,
                            MockNodeInstanceContext,
                            MockRelationshipSubjectContext)
from openstack_plugin_common import (NeutronClientWithSugar,
                                     OPENSTACK_ID_PROPERTY,
                                     OPENSTACK_TYPE_PROPERTY)
from cloudify.exceptions import OperationRetry, NonRecoverableError
from cloudify.state import current_ctx


class TestPort(unittest.TestCase):

    def tearDown(self):
        current_ctx.clear()
        super(TestPort, self).tearDown()

    def test_port_delete(self):
        node_props = {
            'fixed_ip': '',
            'port': {
                'allowed_address_pairs': [{
                    'ip_address': '1.2.3.4'
                }]}}
        mock_neutron = MockNeutronClient(update=True)
        _ctx = self._get_mock_ctx_with_node_properties(node_props)
        current_ctx.set(_ctx)
        with mock.patch('neutron_plugin.port.ctx', _ctx):
            # remove new ip
            port = {'fixed_ips': [],
                    'allowed_address_pairs': [{'ip_address': '1.2.3.4'},
                                              {'ip_address': '5.6.7.8'}],
                    'mac_address': 'abc-edf'}
            neutron_plugin.port._port_delete(mock_neutron, "port_id", port)
            self.assertEqual(
                {'port': {'allowed_address_pairs': [{
                    'ip_address': '5.6.7.8'}]}},
                mock_neutron.body)

    @mock.patch('openstack_plugin_common._handle_kw')
    @mock.patch('openstack_plugin_common'
                '._check_valid_resource_id_with_operation',
                autospec=True, return_value=True)
    def test_delete(self, *_):
        node_props = {
            'fixed_ip': '',
            'port': {
                'allowed_address_pairs': [{
                    'ip_address': '1.2.3.4'
                }]}}
        mock_neutron = MockNeutronClient(update=True)
        _ctx = self._get_mock_ctx_with_node_properties(node_props)
        _ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY] = 'test-sg-id'
        _ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY] = 'port'
        current_ctx.set(_ctx)
        with mock.patch('neutron_plugin.port.ctx', _ctx):
            port = {'fixed_ips': [],
                    'allowed_address_pairs': [{'ip_address': '1.2.3.4'},
                                              {'ip_address': '5.6.7.8'}],
                    'mac_address': 'abc-edf'}
            with mock.patch(
                'neutron_plugin.port.use_external_resource',
                mock.Mock(return_value=port)
            ):
                neutron_plugin.port.delete(mock_neutron)
                self.assertEqual(
                    {'port': {'allowed_address_pairs': [{
                        'ip_address': '5.6.7.8'}]}},
                    mock_neutron.body)

    def test_port_update(self):
        node_props = {
            'fixed_ip': '',
            'resource_id': 'resource_id',
            'port': {
                'allowed_address_pairs': [{
                    'ip_address': '1.2.3.4'
                }]}}
        mock_neutron = MockNeutronClient(update=True)
        _ctx = self._get_mock_ctx_with_node_properties(node_props)
        current_ctx.set(_ctx)
        with mock.patch('neutron_plugin.port.ctx', _ctx):
            port = {'fixed_ips': [],
                    'mac_address': 'abc-edf'}
            # add new ip
            neutron_plugin.port._port_update(mock_neutron, "port_id", {}, port)
            self.assertEqual(
                {
                    'fixed_ip_address': None,
                    'allowed_address_pairs': [{'ip_address': '1.2.3.4'}],
                    'mac_address': 'abc-edf'
                },
                _ctx.instance.runtime_properties)
            # readd same ip
            port = {'fixed_ips': [],
                    'allowed_address_pairs': [{'ip_address': '1.2.3.4'}],
                    'mac_address': 'abc-edf'}
            with self.assertRaises(NonRecoverableError):
                neutron_plugin.port._port_update(mock_neutron, "port_id",
                                                 {}, port)

    @mock.patch('openstack_plugin_common._handle_kw')
    @mock.patch('openstack_plugin_common'
                '._check_valid_resource_id_with_operation',
                autospec=True, return_value=True)
    def test_create(self, *_):
        node_props = {
            'fixed_ip': '',
            'resource_id': 'resource_id',
            'port': {
                'allowed_address_pairs': [{
                    'ip_address': '1.2.3.4'
                }]}}
        mock_neutron = MockNeutronClient(update=True)
        _ctx = self._get_mock_ctx_with_node_properties(node_props)
        _ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY] = 'test-sg-id'
        _ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY] = 'port'
        current_ctx.set(_ctx)
        with mock.patch('neutron_plugin.port.ctx', _ctx):
            port = {'fixed_ips': [],
                    'allowed_address_pairs': [{'ip_address': '5.6.7.8'}],
                    'mac_address': 'abc-edf'}
            with mock.patch(
                'neutron_plugin.port.use_external_resource',
                mock.Mock(return_value=port)
            ):
                neutron_plugin.port.create(mock_neutron, {})
                self.assertEqual(
                    {'port': {'allowed_address_pairs': [{
                        'ip_address': '5.6.7.8'
                    }, {
                        'ip_address': '1.2.3.4'
                    }]}},
                    mock_neutron.body)

    def test_fixed_ips_no_fixed_ips(self):
        node_props = {'fixed_ip': ''}
        mock_neutron = MockNeutronClient(update=True)

        with mock.patch(
                'neutron_plugin.port.'
                'get_openstack_id_of_single_connected_node_by_openstack_type',
                self._get_connected_subnets_mock(return_empty=True)):
            with mock.patch(
                    'neutron_plugin.port.ctx',
                    self._get_mock_ctx_with_node_properties(node_props)):

                port = {}
                neutron_plugin.port._handle_fixed_ips(port, mock_neutron)

        self.assertNotIn('fixed_ips', port)

    def test_fixed_ips_subnet_only(self):
        node_props = {'fixed_ip': ''}
        mock_neutron = MockNeutronClient(update=True)

        with mock.patch(
                'neutron_plugin.port.'
                'get_openstack_ids_of_connected_nodes_by_openstack_type',
                self._get_connected_subnets_mock(return_empty=False)):
            with mock.patch(
                    'neutron_plugin.port.ctx',
                    self._get_mock_ctx_with_node_properties(node_props)):

                port = {}
                neutron_plugin.port._handle_fixed_ips(port, mock_neutron)

        self.assertEquals([{'subnet_id': 'some-subnet-id'}],
                          port.get('fixed_ips'))

    def test_fixed_ips_ip_address_only(self):
        node_props = {'fixed_ip': '1.2.3.4'}
        mock_neutron = MockNeutronClient(update=True)

        with mock.patch(
                'neutron_plugin.port.'
                'get_openstack_id_of_single_connected_node_by_openstack_type',
                self._get_connected_subnets_mock(return_empty=True)):
            with mock.patch(
                    'neutron_plugin.port.ctx',
                    self._get_mock_ctx_with_node_properties(node_props)):

                port = {}
                neutron_plugin.port._handle_fixed_ips(port, mock_neutron)

        self.assertEquals([{'ip_address': '1.2.3.4'}],
                          port.get('fixed_ips'))

    def test_fixed_ips_subnet_and_ip_address(self):
        node_props = {'fixed_ip': '1.2.3.4'}
        mock_neutron = MockNeutronClient(update=True)

        with mock.patch(
                'neutron_plugin.port.'
                'get_openstack_ids_of_connected_nodes_by_openstack_type',
                self._get_connected_subnets_mock(return_empty=False)):
            with mock.patch(
                    'neutron_plugin.port.ctx',
                    self._get_mock_ctx_with_node_properties(node_props)):

                port = {}
                neutron_plugin.port._handle_fixed_ips(port, mock_neutron)

        self.assertEquals([{'ip_address': '1.2.3.4',
                            'subnet_id': 'some-subnet-id'}],
                          port.get('fixed_ips'))

    @staticmethod
    def _get_connected_subnets_mock(return_empty=True):
        return lambda *args, **kw: None if return_empty else ['some-subnet-id']

    @staticmethod
    def _get_mock_ctx_with_node_properties(properties):
        return MockCloudifyContext(node_id='test_node_id',
                                   properties=properties)


class MockNeutronClient(NeutronClientWithSugar):
    """A fake neutron client with hard-coded test data."""
    def __init__(self, update):
        self.update = update
        self.body = {'port': {'id': 'test-id', 'security_groups': []}}

    def show_port(self, *_):
        return self.body

    def delete_port(self, *_):
        pass

    def update_port(self, _, b, **__):
        if self.update:
            self.body.update(b)
        return

    def cosmo_get(self, *_, **__):
        return self.body['port']

    def show_subnet(self, subnet_id=None):
        subnet = {
            'subnet': {
                'id': subnet_id,
            }
        }
        if subnet_id == 'some-subnet-id':
            subnet['subnet']['cidr'] = '1.2.3.0/24'
        else:
            subnet['subnet']['cidr'] = '2.3.4.0/24'
        return subnet


class TestPortSG(unittest.TestCase):
    @mock.patch('openstack_plugin_common._handle_kw')
    @mock.patch('openstack_plugin_common'
                '._check_valid_resource_id_with_operation',
                autospec=True, return_value=True)
    def test_connect_sg_to_port(self, *_):
        mock_neutron = MockNeutronClient(update=True)
        ctx = MockCloudifyContext(
            source=MockRelationshipSubjectContext(node=mock.MagicMock(),
                                                  instance=mock.MagicMock()),
            target=MockRelationshipSubjectContext(
                node=mock.MagicMock(),
                instance=MockNodeInstanceContext(
                    runtime_properties={
                        OPENSTACK_ID_PROPERTY: 'test-sg-id',
                        OPENSTACK_TYPE_PROPERTY: SG_OPENSTACK_TYPE})))

        with mock.patch('neutron_plugin.port.ctx', ctx):
            neutron_plugin.port.connect_security_group(mock_neutron)
            self.assertIsNone(ctx.operation._operation_retry)

    @mock.patch('openstack_plugin_common._handle_kw')
    @mock.patch('openstack_plugin_common'
                '._check_valid_resource_id_with_operation',
                autospec=True, return_value=True)
    def test_connect_sg_to_port_race_condition(self, *_):
        mock_neutron = MockNeutronClient(update=False)

        ctx = MockCloudifyContext(
            source=MockRelationshipSubjectContext(node=mock.MagicMock(),
                                                  instance=mock.MagicMock()),
            target=MockRelationshipSubjectContext(
                node=mock.MagicMock(),
                instance=MockNodeInstanceContext(
                    runtime_properties={
                        OPENSTACK_ID_PROPERTY: 'test-sg-id',
                        OPENSTACK_TYPE_PROPERTY: SG_OPENSTACK_TYPE})))
        with mock.patch('neutron_plugin.port.ctx', ctx):
            neutron_plugin.port.connect_security_group(mock_neutron, ctx=ctx)
            self.assertIsInstance(ctx.operation._operation_retry,
                                  OperationRetry)

    @mock.patch('openstack_plugin_common._handle_kw')
    @mock.patch('openstack_plugin_common'
                '._check_valid_resource_id_with_operation',
                autospec=True, return_value=True)
    def test_disconnect_sg_to_port(self, *_):
        mock_neutron = MockNeutronClient(update=True)
        ctx = MockCloudifyContext(
            source=MockRelationshipSubjectContext(node=mock.MagicMock(),
                                                  instance=mock.MagicMock()),
            target=MockRelationshipSubjectContext(
                node=mock.MagicMock(),
                instance=MockNodeInstanceContext(
                    runtime_properties={
                        OPENSTACK_ID_PROPERTY: 'test-sg-id',
                        OPENSTACK_TYPE_PROPERTY: SG_OPENSTACK_TYPE})))

        with mock.patch('neutron_plugin.port.ctx', ctx):
            neutron_plugin.port.disconnect_security_group(mock_neutron)
            self.assertIsNone(ctx.operation._operation_retry)
