from builtins import object
import mock
import unittest

from cloudify.context import NODE_INSTANCE
from cloudify.exceptions import NonRecoverableError
from cloudify.mocks import (
    MockContext,
    MockNodeInstanceContext,
    MockNodeContext,
    MockRelationshipContext,
    MockRelationshipSubjectContext
)
from openstack_plugin_common import (
    OPENSTACK_ID_PROPERTY,
    OPENSTACK_NAME_PROPERTY,
    OPENSTACK_TYPE_PROPERTY
)
from neutron_plugin.rbac_policy import (
    RBAC_POLICY_OPENSTACK_TYPE,
    RBAC_POLICY_APPLIED_FOR_RELATIONSHIP_TYPE
)

import neutron_plugin


class TestRBACPolicy(unittest.TestCase):
    test_node_instance_id = 'test-rbac-policy-instance-id'
    test_tenant_id = '11111111111111111111'
    test_os_rbac_policy_id = '222222222222222'
    test_os_network_id = '333333333333333'
    test_deployment_id = 'test-deployment-id'

    class MockRBACPolicyOS(object):
        def __init__(self,
                     id,
                     action,
                     object_id,
                     object_type='network',
                     target_tenant='*'):
            self._id = id
            self._action = action
            self._object_id = object_id
            self._object_type = object_type
            self._target_tenant = target_tenant

        @property
        def id(self):
            return self._id

        @property
        def action(self):
            return self._action

        @property
        def object_id(self):
            return self._object_id

        @property
        def object_type(self):
            return self._object_type

        @property
        def target_tenant(self):
            return self._target_tenant

        def to_dict(self):
            return dict(
                [(k.strip('_'), v) for k, v in vars(self).items()]
            )

    def mock_neutron_client(self, mock_rbac_policy):
        neutron_client = mock.MagicMock()

        neutron_client.cosmo_get_if_exists.return_value = mock_rbac_policy
        neutron_client.get_name_from_resource.return_value = None
        neutron_client.get_id_from_resource.return_value = \
            self.test_os_rbac_policy_id
        neutron_client.cosmo_delete_resource = mock.MagicMock()
        neutron_client.create_rbac_policy.return_value = {
            'rbac_policy': mock_rbac_policy.to_dict()
        }
        neutron_client.show_rbac_policy.return_value = mock_rbac_policy
        neutron_client.list_rbac_policies.return_value = {
            'rbac_policies': [mock_rbac_policy.to_dict()]
        }

        return neutron_client

    def mock_ctx(self,
                 test_properties,
                 test_node_instance_id,
                 test_deployment_id,
                 runtime_properties=None,
                 test_relationships=None):

        ctx = MockContext()
        ctx.node = MockNodeContext(properties=test_properties)
        ctx.instance = MockNodeInstanceContext(
            id=test_node_instance_id,
            runtime_properties=runtime_properties or {},
            relationships=test_relationships or []
        )
        ctx.deployment = mock.Mock()
        ctx.deployment.id = test_deployment_id
        ctx.bootstrap_context = mock.Mock()
        setattr(ctx.bootstrap_context, 'resources_prefix', '')
        ctx.type = NODE_INSTANCE
        ctx.logger = mock.Mock()

        return ctx

    def mock_properties(self,
                        use_external_resource=False,
                        create_if_missing=False,
                        resource_id='',
                        include_reference=True):
        rbac_properties = {
            'target_tenant': self.test_tenant_id,
            'action': 'access_as_shared'
        }

        if include_reference:
            rbac_properties['object_type'] = 'network'
            rbac_properties['object_id'] = self.test_os_network_id

        properties = {
            'resource_id': resource_id,
            'use_external_resource': use_external_resource,
            'create_if_missing': create_if_missing,
            RBAC_POLICY_OPENSTACK_TYPE: rbac_properties
        }

        return properties

    def mock_relationship(self,
                          type=RBAC_POLICY_APPLIED_FOR_RELATIONSHIP_TYPE,
                          runtime_properties=None):

        class _MockRelationshipContext(MockRelationshipContext):

            @property
            def type_hierarchy(self):
                return [self.type]

        return _MockRelationshipContext(
            MockRelationshipSubjectContext(
                node=None,
                instance=MockNodeInstanceContext(
                    runtime_properties=runtime_properties or {},
                )
            ),
            type=type
        )

    def mock_all(self, relationships=None, **kwargs):
        ctx = self.mock_ctx(
            self.mock_properties(**kwargs),
            self.test_node_instance_id,
            self.test_deployment_id,
            {
                OPENSTACK_ID_PROPERTY: self.test_node_instance_id,
                OPENSTACK_NAME_PROPERTY: None,
                OPENSTACK_TYPE_PROPERTY: RBAC_POLICY_OPENSTACK_TYPE,
            },
            relationships or []
        )
        neutron_plugin.rbac_policy.ctx = ctx
        mocked_rbac_policy = self.MockRBACPolicyOS(
            id=self.test_os_rbac_policy_id,
            object_id=self.test_os_network_id,
            action='access_as_shared',
            target_tenant=self.test_tenant_id
        )
        neutron_client = self.mock_neutron_client(mocked_rbac_policy)

        return ctx, neutron_client, mocked_rbac_policy

    @mock.patch(
        'openstack_plugin_common._handle_kw',
        autospec=True,
        return_value=None
    )
    @mock.patch('openstack_plugin_common'
                '._check_valid_resource_id_with_operation',
                autospec=True, return_value=True)
    def test_create_and_delete(self, *_):
        # given
        ctx, neutron_client, _ = self.mock_all()

        # when (create)
        neutron_plugin.rbac_policy.create(neutron_client, {})

        # then (create)
        neutron_client.create_rbac_policy.assert_called_once()

        self.assertEqual(
            None,
            ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY]
        )
        self.assertEqual(
            self.test_os_rbac_policy_id,
            ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY]
        )
        self.assertEqual(
            RBAC_POLICY_OPENSTACK_TYPE,
            ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY]
        )

        # when (delete)
        neutron_plugin.rbac_policy.delete(neutron_client)

        # then (delete)
        neutron_client.cosmo_delete_resource.assert_called_once_with(
            RBAC_POLICY_OPENSTACK_TYPE,
            self.test_os_rbac_policy_id
        )
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
    def test_create_and_delete_external_resource(self, *_):
        # given
        ctx, neutron_client, _ = self.mock_all(use_external_resource=True)

        # when (create)
        neutron_plugin.rbac_policy.create(neutron_client, {})

        # then (create)
        neutron_client.create_rbac_policy.assert_not_called()

        self.assertEqual(
            None,
            ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY]
        )
        self.assertEqual(
            self.test_os_rbac_policy_id,
            ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY]
        )
        self.assertEqual(
            RBAC_POLICY_OPENSTACK_TYPE,
            ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY]
        )

        # when (delete)
        neutron_plugin.rbac_policy.delete(neutron_client)

        # then (delete)
        neutron_client.cosmo_delete_resource.assert_not_called()

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
    def test_create_and_delete_using_relationship(self, *_):
        # given
        ctx, neutron_client, _ = self.mock_all(
            include_reference=False,
            relationships=[
                self.mock_relationship(
                    runtime_properties={
                        OPENSTACK_TYPE_PROPERTY: 'network',
                        OPENSTACK_ID_PROPERTY: self.test_os_network_id
                    }
                ),
                self.mock_relationship(
                    type='cloudify.relationships.depends_on'
                )
            ]
        )

        # when (create)
        neutron_plugin.rbac_policy.create(neutron_client, {})

        # then (create)
        neutron_client.create_rbac_policy.assert_called_once()

        self.assertEqual(
            None,
            ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY]
        )
        self.assertEqual(
            self.test_os_rbac_policy_id,
            ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY]
        )
        self.assertEqual(
            RBAC_POLICY_OPENSTACK_TYPE,
            ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY]
        )

        # when (delete)
        neutron_plugin.rbac_policy.delete(neutron_client)

        # then (delete)
        neutron_client.cosmo_delete_resource.assert_called_once_with(
            RBAC_POLICY_OPENSTACK_TYPE,
            self.test_os_rbac_policy_id
        )
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
    def test_fail_create_using_multiple_relationships(self, *_):
        # given
        ctx, neutron_client, _ = self.mock_all(
            include_reference=False,
            relationships=[
                self.mock_relationship(
                    runtime_properties={
                        OPENSTACK_TYPE_PROPERTY: 'network',
                        OPENSTACK_ID_PROPERTY: self.test_os_network_id
                    }
                ),
                self.mock_relationship()
            ]
        )

        # when + then
        with self.assertRaises(NonRecoverableError):
            neutron_plugin.rbac_policy.create(neutron_client, {})

    @mock.patch(
        'openstack_plugin_common._handle_kw',
        autospec=True,
        return_value=None
    )
    @mock.patch('openstack_plugin_common'
                '._check_valid_resource_id_with_operation',
                autospec=True, return_value=True)
    def test_fail_create_using_relationship_with_missing_data(self, *_):
        # given
        ctx, neutron_client, _ = self.mock_all(
            include_reference=False,
            relationships=[self.mock_relationship()]
        )

        # when
        neutron_plugin.rbac_policy.create(neutron_client, {})

        # then
        neutron_client.create_rbac_policy.assert_called_once_with({
            'rbac_policy': {
                'target_tenant': self.test_tenant_id,
                'action': 'access_as_shared'
            }
        })
        # should cause "Bad Request" openstack API error bacause of lack
        # "object_id" and "object_type" fields

    @mock.patch(
        'openstack_plugin_common._handle_kw',
        autospec=True,
        return_value=None
    )
    @mock.patch('openstack_plugin_common'
                '._check_valid_resource_id_with_operation',
                autospec=True, return_value=True)
    def test_fail_create_using_relationship_and_properties(self, *_):
        # given
        ctx, neutron_client, _ = self.mock_all(
            relationships=[
                self.mock_relationship(
                    runtime_properties={
                        OPENSTACK_TYPE_PROPERTY: 'network',
                        OPENSTACK_ID_PROPERTY: self.test_os_network_id
                    }
                )
            ]
        )

        # when + then
        with self.assertRaises(NonRecoverableError):
            neutron_plugin.rbac_policy.create(neutron_client, {})

    @mock.patch(
        'openstack_plugin_common._handle_kw',
        autospec=True,
        return_value=None
    )
    @mock.patch('openstack_plugin_common'
                '._check_valid_resource_id_with_operation',
                autospec=True, return_value=True)
    def test_create_and_delete_using_args(self, *_):
        # given
        ctx, neutron_client, _ = self.mock_all(
            include_reference=False,
        )

        # when (create)
        neutron_plugin.rbac_policy.create(
            neutron_client,
            self.mock_properties()
        )

        # then (create)
        neutron_client.create_rbac_policy.assert_called_once()

        self.assertEqual(
            None,
            ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY]
        )
        self.assertEqual(
            self.test_os_rbac_policy_id,
            ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY]
        )
        self.assertEqual(
            RBAC_POLICY_OPENSTACK_TYPE,
            ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY]
        )

        # when (delete)
        neutron_plugin.rbac_policy.delete(neutron_client)

        # then (delete)
        neutron_client.cosmo_delete_resource.assert_called_once_with(
            RBAC_POLICY_OPENSTACK_TYPE,
            self.test_os_rbac_policy_id
        )
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
    def test_fail_create_using_relationship_and_args(self, *_):
        # given
        ctx, neutron_client, _ = self.mock_all(
            include_reference=False,
            relationships=[
                self.mock_relationship(
                    runtime_properties={
                        OPENSTACK_TYPE_PROPERTY: 'network',
                        OPENSTACK_ID_PROPERTY: self.test_os_network_id
                    }
                )
            ]
        )

        # when + then
        with self.assertRaises(NonRecoverableError):
            neutron_plugin.rbac_policy.create(
                neutron_client,
                self.mock_properties()
            )

    @mock.patch(
        'openstack_plugin_common._handle_kw',
        autospec=True,
        return_value=None
    )
    @mock.patch('openstack_plugin_common'
                '._check_valid_resource_id_with_operation',
                autospec=True, return_value=True)
    def test_list(self, *_):
        # given
        ctx, neutron_client, _ = self.mock_all()

        # when
        neutron_plugin.rbac_policy.list_rbac_policies(neutron_client, {})

        # then
        rbac_policies_list_key = '{}_list'.format(RBAC_POLICY_OPENSTACK_TYPE)
        self.assertIn(rbac_policies_list_key, ctx.instance.runtime_properties)
        self.assertEqual(
            [{
                'target_tenant': self.test_tenant_id,
                'action': 'access_as_shared',
                'object_type': 'network',
                'object_id': self.test_os_network_id,
                'id': self.test_os_rbac_policy_id
            }],
            ctx.instance.runtime_properties[rbac_policies_list_key]
        )

    @mock.patch(
        'openstack_plugin_common._handle_kw',
        autospec=True,
        return_value=None
    )
    @mock.patch('openstack_plugin_common'
                '._check_valid_resource_id_with_operation',
                autospec=True, return_value=True)
    def test_find_and_delete(self, *_):
        # given
        ctx, neutron_client, _ = self.mock_all()

        # when
        neutron_plugin.rbac_policy.find_and_delete(neutron_client, {})

        # then
        neutron_client.list_rbac_policies.assert_called_once()
        neutron_client.cosmo_delete_resource.assert_called_once_with(
            RBAC_POLICY_OPENSTACK_TYPE,
            self.test_os_rbac_policy_id
        )
