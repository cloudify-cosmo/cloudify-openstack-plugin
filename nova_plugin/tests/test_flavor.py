from builtins import object
import mock
import unittest

from cloudify.context import NODE_INSTANCE
from cloudify.context import BootstrapContext
from cloudify.state import current_ctx
import openstack_plugin_common.tests.test as common_test

from cloudify.mocks import (
    MockContext,
    MockNodeInstanceContext,
    MockNodeContext
)
from openstack_plugin_common import (
    OPENSTACK_ID_PROPERTY,
    OPENSTACK_NAME_PROPERTY,
    OPENSTACK_TYPE_PROPERTY
)
from nova_plugin.flavor import (
    FLAVOR_OPENSTACK_TYPE,
    EXTRA_SPECS_PROPERTY,
    TENANTS_PROPERTY
)
import nova_plugin


class TestFlavor(unittest.TestCase):
    test_id = 'test-id'
    test_name = 'test-name'
    updated_name = 'updated-name'
    test_deployment_id = 'test-deployment-id'

    class MockFlavorOS(object):
        def __init__(self, id, name):
            self._id = id
            self._name = name
            self._set_keys_called = False
            self._set_keys_last_call_params = {}

        @property
        def id(self):
            return self._id

        @property
        def name(self):
            return self._name

        def set_keys(self, extra_specs):
            self._set_keys_called = True
            self._set_keys_last_call_params = extra_specs

        def assert_set_keys_called_with(self, test, params):
            test.assertTrue(self._set_keys_called)
            test.assertEquals(self._set_keys_last_call_params, params)

        def to_dict(self):
            return {'name': self.name, 'id': self.id}

    def mock_nova_client(self, mock_flavor):
        nova_client = mock.MagicMock()
        nova_client.flavors.create.return_value = mock_flavor
        nova_client.flavors.list.return_value = [mock_flavor]
        nova_client.flavors.find.return_value = mock.MagicMock(
            id=self.test_name
        )
        nova_client.flavor_access.add_tenant_access = mock.MagicMock()

        return nova_client

    def mock_ctx(self,
                 test_vars,
                 test_id,
                 test_deployment_id,
                 runtime_properties=None):
        ctx = MockContext()

        ctx.node = MockNodeContext(properties=test_vars)
        ctx.bootstrap_context = BootstrapContext(
            common_test.BOOTSTRAP_CONTEXTS_WITHOUT_PREFIX[0]
        )
        ctx.instance = MockNodeInstanceContext(
            id=test_id,
            runtime_properties=runtime_properties or {}
        )
        ctx.deployment = mock.Mock()
        ctx.deployment.id = test_deployment_id
        ctx.type = NODE_INSTANCE
        ctx.logger = mock.Mock()

        current_ctx.set(ctx)
        return ctx

    @mock.patch(
        'openstack_plugin_common._handle_kw',
        autospec=True,
        return_value=None
    )
    @mock.patch('openstack_plugin_common'
                '._check_valid_resource_id_with_operation',
                autospec=True, return_value=True)
    def test_flavor_create_and_delete(self, *_):
        # given
        test_vars = {
            'flavor': {},
            'resource_id': ''
        }

        ctx = self.mock_ctx(test_vars, self.test_id, self.test_deployment_id)
        nova_plugin.flavor.ctx = ctx
        mock_flavor = self.MockFlavorOS(self.test_id, self.test_name)
        nova_client = self.mock_nova_client(mock_flavor)

        # when (create)
        nova_plugin.flavor.create(nova_client, {})

        # then (create)
        self.assertEqual(
            self.test_name,
            ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY]
        )
        self.assertEqual(
            self.test_id,
            ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY]
        )
        self.assertEqual(
            FLAVOR_OPENSTACK_TYPE,
            ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY]
        )

        # when (delete)
        nova_plugin.flavor.delete(nova_client=nova_client)

        # then (delete)
        self.assertNotIn(
            OPENSTACK_ID_PROPERTY,
            ctx.instance.runtime_properties
        )
        self.assertNotIn(
            OPENSTACK_NAME_PROPERTY,
            ctx.instance.runtime_properties
        )
        self.assertNotIn(
            OPENSTACK_TYPE_PROPERTY,
            ctx.instance.runtime_properties
        )

    @mock.patch(
        'openstack_plugin_common._handle_kw',
        autospec=True,
        return_value=None
    )
    @mock.patch('openstack_plugin_common'
                '._check_valid_resource_id_with_operation',
                autospec=True, return_value=True)
    def test_flavor_create_and_delete_with_extra_specs_and_tenants(self, *_):
        # given
        test_vars_tenant_id = 'some_tenant_id'
        test_vars_tenants = [test_vars_tenant_id]
        test_vars_extra_specs = {
            'key1': 'value1',
            'key2': 'value2'
        }
        test_vars = {
            'flavor': {},
            'extra_specs': test_vars_extra_specs,
            'tenants': test_vars_tenants,
            'resource_id': ''
        }

        ctx = self.mock_ctx(test_vars, self.test_id, self.test_deployment_id)
        nova_plugin.flavor.ctx = ctx
        mock_flavor = self.MockFlavorOS(self.test_id, self.test_name)
        nova_client = self.mock_nova_client(mock_flavor)

        # when (create)
        nova_plugin.flavor.create(nova_client, {})

        # then (create)
        mock_flavor.assert_set_keys_called_with(self, test_vars_extra_specs)
        nova_client.flavor_access.add_tenant_access.assert_called_once_with(
            mock_flavor,
            test_vars_tenant_id
        )

        self.assertEqual(
            self.test_name,
            ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY]
        )
        self.assertEqual(
            self.test_id,
            ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY]
        )
        self.assertEqual(
            FLAVOR_OPENSTACK_TYPE,
            ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY]
        )
        self.assertEqual(
            test_vars_extra_specs,
            ctx.instance.runtime_properties[EXTRA_SPECS_PROPERTY]
        )
        self.assertEqual(
            test_vars_tenants,
            ctx.instance.runtime_properties[TENANTS_PROPERTY]
        )

        # when (delete)
        nova_plugin.flavor.delete(nova_client=nova_client)

        # then (delete)
        self.assertNotIn(
            OPENSTACK_ID_PROPERTY,
            ctx.instance.runtime_properties
        )
        self.assertNotIn(
            OPENSTACK_NAME_PROPERTY,
            ctx.instance.runtime_properties
        )
        self.assertNotIn(
            OPENSTACK_TYPE_PROPERTY,
            ctx.instance.runtime_properties
        )
        self.assertNotIn(
            EXTRA_SPECS_PROPERTY,
            ctx.instance.runtime_properties
        )
        self.assertNotIn(
            TENANTS_PROPERTY,
            ctx.instance.runtime_properties
        )

    @mock.patch('openstack_plugin_common'
                '._check_valid_resource_id_with_operation',
                autospec=True, return_value=True)
    def test_list_flavors(self, *_):
        # given
        test_vars = {
            'flavor': {},
            'resource_id': ''
        }

        ctx = self.mock_ctx(
            test_vars,
            self.test_id,
            self.test_deployment_id,
            {OPENSTACK_ID_PROPERTY: self.test_id}
        )
        mock_flavor = self.MockFlavorOS(self.test_id, self.test_name)
        nova_client = self.mock_nova_client(mock_flavor)
        nova_plugin.flavor.ctx = ctx

        # when
        nova_plugin.flavor.list_flavors(args={}, nova_client=nova_client)

        # then
        flavor_list = FLAVOR_OPENSTACK_TYPE + '_list'
        self.assertIn(flavor_list, ctx.instance.runtime_properties)
        self.assertEqual(1, len(ctx.instance.runtime_properties[flavor_list]))
