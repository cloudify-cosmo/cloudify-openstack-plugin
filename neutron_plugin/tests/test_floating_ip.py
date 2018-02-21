import os
import unittest
import mock

from cloudify.test_utils import workflow_test
from cloudify.mocks import MockNodeInstanceContext

from neutron_plugin.floatingip import (
    FLOATINGIP_OPENSTACK_TYPE, FLOATING_NETWORK_ERROR_PREFIX)
from openstack_plugin_common import OPENSTACK_ID_PROPERTY


class FloatingIPTest(unittest.TestCase):
    @mock.patch('neutron_plugin.network.create')
    @mock.patch('neutronclient.v2_0.client.Client.create_floatingip')
    @workflow_test(os.path.join('resources', 'test_fip_rel.yaml'),
                   copy_plugin_yaml=True)
    def test_network_rel(self, cfy_local, *_):
        def _mock_rel(*_):
            return MockNodeInstanceContext(runtime_properties={
                OPENSTACK_ID_PROPERTY: 'my-id'
            })

        def _mock_create(_, fip):
            self.assertEqual(fip[FLOATINGIP_OPENSTACK_TYPE][
                                 'floating_network_id'], 'my-id')
            return {FLOATINGIP_OPENSTACK_TYPE: {
                'id': '1234',
                'floating_ip_address': '1.2.3.4'
            }}

        with mock.patch('neutronclient.v2_0.client.Client.create_floatingip',
                        new=_mock_create):
            with mock.patch(
                    'neutron_plugin.floatingip.get_single_connected_node_by_'
                    'openstack_type', new=_mock_rel):
                cfy_local.execute('install')

    @mock.patch('neutron_plugin.network.create')
    @mock.patch('neutronclient.v2_0.client.Client.create_floatingip')
    @workflow_test(os.path.join('resources', 'test_fip_rel_and_id.yaml'),
                   copy_plugin_yaml=True)
    def test_network_rel_and_id(self, cfy_local, *_):
        def _mock_rel(*_):
            return MockNodeInstanceContext(runtime_properties={
                OPENSTACK_ID_PROPERTY: 'my-id'
            })

        with mock.patch('neutron_plugin.floatingip.get_single_connected_node_'
                        'by_openstack_type',
                        new=_mock_rel):
            with self.assertRaises(Exception) as ex:
                cfy_local.execute('install')

            self.assertTrue(FLOATING_NETWORK_ERROR_PREFIX in str(ex.exception))
