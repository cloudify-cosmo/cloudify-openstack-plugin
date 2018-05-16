import mock
import unittest

from cloudify.context import NODE_INSTANCE
from cloudify.exceptions import NonRecoverableError
from cloudify.context import BootstrapContext
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
from keystone_plugin.project import (
    PROJECT_OPENSTACK_TYPE,
    QUOTA
)
import keystone_plugin


class TestProject(unittest.TestCase):

    test_id = 'test-id'
    test_name = 'test-name'
    updated_name = 'updated-name'
    test_deployment_id = 'test-deployment-id'
    test_user = 'test-user'
    test_role = 'test-role'

    class MockProjectOS:
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

        def find(self, *_, **__):
            return mock.MagicMock(id='test-role')

        def grant(self, role, user, *_, **__):
            self._users[user] = role

        def to_dict(self):
            return {'name': self.name, 'id': self.id}

    def mock_keystone_client(self, mock_project):
        keystone_client = mock.MagicMock()
        keystone_client.projects.create.return_value = mock_project
        keystone_client.projects.list.return_value = \
            {'projects': [mock_project]}
        keystone_client.users.find.return_value = mock.MagicMock(
            id=self.test_user)
        keystone_client.projects.update.return_value = self.MockProjectOS(
            self.id, self.updated_name)
        keystone_client.roles = mock_project
        return keystone_client

    def mock_ctx(self, test_vars, test_id,
                 test_deployment_id, runtime_properties=None):
        ctx = MockContext()
        ctx.node = MockNodeContext(properties=test_vars)
        ctx.bootstrap_context = BootstrapContext(
            common_test.BOOTSTRAP_CONTEXTS_WITHOUT_PREFIX[0])
        ctx.instance = MockNodeInstanceContext(
            id=test_id, runtime_properties=runtime_properties or {})
        ctx.deployment = mock.Mock()
        ctx.deployment.id = test_deployment_id
        ctx.type = NODE_INSTANCE
        ctx.logger = mock.Mock()
        return ctx

    @mock.patch('openstack_plugin_common._put_client_in_kw',
                autospec=True, return_value=None)
    def test_keystone_project_create_and_delete(self, *_):
        quota = {'nova': {'cpu': 120},
                 'neutron': {'networks': 100}}
        test_vars = {
            'project': {},
            'resource_id': '',
            'quota': quota,
            'users': {}
        }

        ctx = self.mock_ctx(test_vars, self.test_id, self.test_deployment_id)
        keystone_plugin.project.ctx = ctx
        mock_project = self.MockProjectOS(self.test_id, self.test_name)
        keystone_client = self.mock_keystone_client(mock_project)
        keystone_plugin.project.create(keystone_client, {})
        self.assertEqual(self.test_name,
                         ctx.instance.runtime_properties[
                             OPENSTACK_NAME_PROPERTY])
        self.assertEqual(self.test_id,
                         ctx.instance.runtime_properties[
                             OPENSTACK_ID_PROPERTY])
        self.assertEqual(PROJECT_OPENSTACK_TYPE,
                         ctx.instance.runtime_properties[
                             OPENSTACK_TYPE_PROPERTY])

        keystone_plugin.project.delete(
            keystone_client=keystone_client,  # keystone_client
            nova_client=mock.MagicMock(),  # nova_client
            cinder_client=mock.MagicMock(),  # cinder_client
            neutron_client=mock.MagicMock())  # neutron_client
        self.assertNotIn(OPENSTACK_ID_PROPERTY,
                         ctx.instance.runtime_properties)
        self.assertNotIn(OPENSTACK_NAME_PROPERTY,
                         ctx.instance.runtime_properties)
        self.assertNotIn(OPENSTACK_TYPE_PROPERTY,
                         ctx.instance.runtime_properties)

    def test_assign_user(self, *_):
        test_vars = {
            'project': {},
            'resource_id': '',
            'quota': {},
            'users': [{'name': self.test_user,
                       'roles': [self.test_role]}]
        }
        ctx = self.mock_ctx(test_vars,
                            self.test_id,
                            self.test_deployment_id,
                            {OPENSTACK_ID_PROPERTY: self.test_id})
        mock_project = self.MockProjectOS(self.test_id, self.test_name)
        keystone_client = self.mock_keystone_client(mock_project)
        keystone_plugin.project.ctx = ctx
        keystone_plugin.project.start(
            {},
            keystone_client=keystone_client,  # keystone_client
            nova_client=mock.MagicMock(),  # nova_client
            cinder_client=mock.MagicMock(),  # cinder_client
            neutron_client=mock.MagicMock())  # neutron_client
        self.assertEqual({self.test_user: self.test_role},
                         mock_project._users)

    def test_assign_users_not_unique(self, *_):
        test_vars = {
            'project': {},
            'resource_id': '',
            'quota': {},
            'users': [{'name': self.test_user,
                       'roles': [self.test_role]},
                      {'name': self.test_user,
                       'roles': [self.test_role]}]
        }
        ctx = self.mock_ctx(test_vars,
                            self.test_id,
                            self.test_deployment_id,
                            {OPENSTACK_ID_PROPERTY: self.test_id})
        mock_project = self.MockProjectOS(self.test_id, self.test_name)
        keystone_client = self.mock_keystone_client(mock_project)
        keystone_plugin.project.ctx = ctx
        with self.assertRaises(NonRecoverableError):
            keystone_plugin.project.start(
                {},
                keystone_client=keystone_client,  # keystone_client
                nova_client=mock.MagicMock(),  # nova_client
                cinder_client=mock.MagicMock(),  # cinder_client
                neutron_client=mock.MagicMock())  # neutron_client

    def test_assign_user_roles_not_unique(self, *_):
        test_vars = {
            'project': {},
            'resource_id': '',
            'quota': {},
            'users': [{'name': self.test_user,
                       'roles': [self.test_role, self.test_role]}]
        }
        ctx = self.mock_ctx(test_vars,
                            self.test_id,
                            self.test_deployment_id,
                            {OPENSTACK_ID_PROPERTY: self.test_id})
        mock_project = self.MockProjectOS(self.test_id, self.test_name)
        keystone_client = self.mock_keystone_client(mock_project)
        keystone_plugin.project.ctx = ctx
        with self.assertRaises(NonRecoverableError):
            keystone_plugin.project.start(
                {},
                keystone_client=keystone_client,  # keystone_client
                nova_client=mock.MagicMock(),  # nova_client
                cinder_client=mock.MagicMock(),  # cinder_client
                neutron_client=mock.MagicMock())  # neutron_client

    def test_update_project(self, *_):
        test_vars = {
            'project': {},
            'resource_id': '',
            'quota': {},
            'users': [{'name': self.test_user,
                       'roles': [self.test_role]}]
        }
        ctx = self.mock_ctx(test_vars,
                            self.test_id,
                            self.test_deployment_id,
                            {OPENSTACK_ID_PROPERTY: self.test_id})
        mock_project = self.MockProjectOS(self.test_id, self.test_name)
        keystone_client = self.mock_keystone_client(mock_project)
        keystone_plugin.project.ctx = ctx
        keystone_plugin.project.update_project(args={},
                                               keystone_client=keystone_client)
        self.assertEqual(self.updated_name,
                         ctx.instance.runtime_properties[
                             OPENSTACK_NAME_PROPERTY])

    def test_list_projects(self, *_):
        test_vars = {
            'project': {},
            'resource_id': '',
            'quota': {},
            'users': [{'name': self.test_user,
                       'roles': [self.test_role]}]
        }
        ctx = self.mock_ctx(test_vars,
                            self.test_id,
                            self.test_deployment_id,
                            {OPENSTACK_ID_PROPERTY: self.test_id})
        mock_project = self.MockProjectOS(self.test_id, self.test_name)
        keystone_client = self.mock_keystone_client(mock_project)
        keystone_plugin.project.ctx = ctx
        keystone_plugin.project.list_projects(args={},
                                              keystone_client=keystone_client)
        project_list = PROJECT_OPENSTACK_TYPE + '_list'
        self.assertIn(project_list, ctx.instance.runtime_properties)
        self.assertEqual(1,
                         len(ctx.instance.runtime_properties[project_list]))

    def test_get_quota(self, *_):
        nova_quota = {'cpu': 120}
        cinder_quota = {'volumes': 30}
        neutron_quota = {'networks': 100}

        quota = {
            'nova': nova_quota,
            'neutron': neutron_quota,
            'cinder': cinder_quota
        }

        test_vars = {
            'project': {},
            'resource_id': '',
            'quota': {},
            'users': [{'name': self.test_user,
                       'roles': [self.test_role]}]
        }

        ctx = self.mock_ctx(test_vars,
                            self.test_id,
                            self.test_deployment_id,
                            {OPENSTACK_ID_PROPERTY: self.test_id})
        keystone_plugin.project.ctx = ctx

        nova_quota_response_mock = mock.MagicMock()
        nova_quota_response_mock.to_dict = mock.MagicMock(
            return_value=nova_quota
        )
        nova_client = mock.MagicMock()
        nova_client.quotas.get = mock.MagicMock(
            return_value=nova_quota_response_mock
        )

        cinder_quota_response_mock = mock.MagicMock()
        cinder_quota_response_mock.to_dict = mock.MagicMock(
            return_value=cinder_quota
        )
        cinder_client = mock.MagicMock()
        cinder_client.quotas.get = mock.MagicMock(
            return_value=cinder_quota_response_mock
        )

        neutron_client = mock.MagicMock()
        neutron_client.show_quota = mock.MagicMock(
            return_value={'quota': neutron_quota}
            # format of neutron client 'show_quota' response
        )

        keystone_plugin.project.get_project_quota(
            nova_client=nova_client,
            cinder_client=cinder_client,
            neutron_client=neutron_client)

        self.assertIn(QUOTA, ctx.instance.runtime_properties)
        self.assertDictEqual(quota, ctx.instance.runtime_properties[QUOTA])
