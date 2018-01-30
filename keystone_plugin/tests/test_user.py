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
from keystone_plugin.user import USER_OPENSTACK_TYPE
import keystone_plugin


class TestUser(unittest.TestCase):

    test_id = 'test-id'
    test_name = 'test-name'
    updated_name = 'updated-name'
    test_deployment_id = 'test-deployment-id'

    class MockUserOS:
        def __init__(self, id, name):
            self._id = id
            self._name = name
            self._users = {}

        @property
        def id(self):
            return self._id

        @property
        def name(self):
            return self._name

        def to_dict(self):
            return {'name': self.name, 'id': self.id}

    def mock_keystone_client(self, mock_user):
        keystone_client = mock.MagicMock()
        keystone_client.users.create.return_value = mock_user
        keystone_client.users.list.return_value = [mock_user]
        keystone_client.users.find.return_value = mock.MagicMock(
            id=self.test_name)
        keystone_client.users.update.return_value = self.MockUserOS(
            self.id, self.updated_name)
        return keystone_client

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
    def test_keystone_user_create_and_delete(self, *_):
        test_vars = {
            'user': {},
            'resource_id': ''
        }

        ctx = self.mock_ctx(test_vars, self.test_id, self.test_deployment_id)
        keystone_plugin.user.ctx = ctx
        mock_user = self.MockUserOS(self.test_id, self.test_name)
        keystone_client = self.mock_keystone_client(mock_user)
        keystone_plugin.user.create(keystone_client, {})
        self.assertEqual(self.test_name,
                         ctx.instance.runtime_properties[
                             OPENSTACK_NAME_PROPERTY])
        self.assertEqual(self.test_id,
                         ctx.instance.runtime_properties[
                             OPENSTACK_ID_PROPERTY])
        self.assertEqual(USER_OPENSTACK_TYPE,
                         ctx.instance.runtime_properties[
                             OPENSTACK_TYPE_PROPERTY])

        keystone_plugin.user.delete(keystone_client=keystone_client)
        self.assertNotIn(OPENSTACK_ID_PROPERTY,
                         ctx.instance.runtime_properties)
        self.assertNotIn(OPENSTACK_NAME_PROPERTY,
                         ctx.instance.runtime_properties)
        self.assertNotIn(OPENSTACK_TYPE_PROPERTY,
                         ctx.instance.runtime_properties)

    def test_update_user(self, *_):
        test_vars = {
            'user': {},
            'resource_id': ''
        }
        ctx = self.mock_ctx(test_vars,
                            self.test_id,
                            self.test_deployment_id,
                            {OPENSTACK_ID_PROPERTY: self.test_id})
        mock_user = self.MockUserOS(self.test_id, self.test_name)
        keystone_client = self.mock_keystone_client(mock_user)
        keystone_plugin.user.ctx = ctx
        keystone_plugin.user.update(args={}, keystone_client=keystone_client)
        self.assertEqual(self.updated_name,
                         ctx.instance.runtime_properties[
                             OPENSTACK_NAME_PROPERTY])

    def test_list_users(self, *_):
        test_vars = {
            'user': {},
            'resource_id': ''
        }
        ctx = self.mock_ctx(test_vars,
                            self.test_id,
                            self.test_deployment_id,
                            {OPENSTACK_ID_PROPERTY: self.test_id})
        mock_user = self.MockUserOS(self.test_id, self.test_name)
        keystone_client = self.mock_keystone_client(mock_user)
        keystone_plugin.user.ctx = ctx
        keystone_plugin.user.list_users(args={},
                                        keystone_client=keystone_client)
        user_list = USER_OPENSTACK_TYPE + '_list'
        self.assertIn(user_list, ctx.instance.runtime_properties)
        self.assertEqual(1, len(ctx.instance.runtime_properties[user_list]))
