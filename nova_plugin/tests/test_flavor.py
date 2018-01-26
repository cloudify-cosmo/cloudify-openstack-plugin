import mock
import unittest

from cloudify.context import NODE_INSTANCE

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
from nova_plugin.flavor import FLAVOR_OPENSTACK_TYPE
import nova_plugin


class TestFlavor(unittest.TestCase):

    test_id = 'test-id'
    test_name = 'test-name'
    updated_name = 'updated-name'
    test_deployment_id = 'test-deployment-id'

    class MockFlavorOS:
        def __init__(self, id, name):
            self._id = id
            self._name = name

        @property
        def id(self):
            return self._id

        @property
        def name(self):
            return self._name

        def to_dict(self):
            return {'name': self.name, 'id': self.id}

    def mock_nova_client(self, mock_flavor):
        nova_client = mock.MagicMock()
        nova_client.flavors.create.return_value = mock_flavor
        nova_client.flavors.list.return_value = [mock_flavor]
        nova_client.flavors.find.return_value = mock.MagicMock(
            id=self.test_name)
        return nova_client

    def mock_ctx(self, test_vars, test_id,
                 test_deployment_id, runtime_properties=None):
        ctx = MockContext()
        ctx.node = MockNodeContext(properties=test_vars)
        ctx.instance = MockNodeInstanceContext(
            id=test_id, runtime_properties=runtime_properties or {})
        ctx.deployment = mock.Mock()
        ctx.deployment.id = test_deployment_id
        ctx.type = NODE_INSTANCE
        ctx.logger = mock.Mock()
        return ctx

    @mock.patch('openstack_plugin_common._put_client_in_kw',
                autospec=True, return_value=None)
    def test_keystone_flavor_create_and_delete(self, *_):
        test_vars = {
            'flavor': {},
            'resource_id': ''
        }

        ctx = self.mock_ctx(test_vars, self.test_id, self.test_deployment_id)
        nova_plugin.flavor.ctx = ctx
        mock_flavor = self.MockFlavorOS(self.test_id, self.test_name)
        nova_client = self.mock_nova_client(mock_flavor)
        nova_plugin.flavor.create(nova_client, {})
        self.assertEqual(self.test_name,
                         ctx.instance.runtime_properties[
                             OPENSTACK_NAME_PROPERTY])
        self.assertEqual(self.test_id,
                         ctx.instance.runtime_properties[
                             OPENSTACK_ID_PROPERTY])
        self.assertEqual(FLAVOR_OPENSTACK_TYPE,
                         ctx.instance.runtime_properties[
                             OPENSTACK_TYPE_PROPERTY])

        nova_plugin.flavor.delete(nova_client=nova_client)
        self.assertNotIn(OPENSTACK_ID_PROPERTY,
                         ctx.instance.runtime_properties)
        self.assertNotIn(OPENSTACK_NAME_PROPERTY,
                         ctx.instance.runtime_properties)
        self.assertNotIn(OPENSTACK_TYPE_PROPERTY,
                         ctx.instance.runtime_properties)

    def test_list_flavors(self, *_):
        test_vars = {
            'flavor': {},
            'resource_id': ''
        }
        ctx = self.mock_ctx(test_vars,
                            self.test_id,
                            self.test_deployment_id,
                            {OPENSTACK_ID_PROPERTY: self.test_id})
        mock_flavor = self.MockFlavorOS(self.test_id, self.test_name)
        nova_client = self.mock_nova_client(mock_flavor)
        nova_plugin.flavor.ctx = ctx
        nova_plugin.flavor.list_flavors(args={}, nova_client=nova_client)
        flavor_list = FLAVOR_OPENSTACK_TYPE + '_list'
        self.assertIn(flavor_list, ctx.instance.runtime_properties)
        self.assertEqual(1, len(ctx.instance.runtime_properties[flavor_list]))
