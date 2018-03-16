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
    OPENSTACK_TYPE_PROPERTY,
    OPENSTACK_RESOURCE_PROPERTY
)
from nova_plugin.host_aggregate import (
    HOST_AGGREGATE_OPENSTACK_TYPE,
    HOSTS_PROPERTY
)
import nova_plugin


class TestHostAggregate(unittest.TestCase):
    test_id = 'test-id'
    test_name = 'test-name'
    existing_test_id = 'existing-test-id'
    existing_test_name = 'existing-test-name'
    updated_name = 'updated-name'
    test_deployment_id = 'test-deployment-id'

    class MockHostAggregateOS:
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

    def mock_nova_client(self,
                         mock_host_aggregate,
                         mocked_updated_host_aggregate=None):
        nova_client = mock.MagicMock()

        nova_client.aggregates.create.return_value = mock_host_aggregate
        nova_client.aggregates.list.return_value = [mock_host_aggregate]
        nova_client.aggregates.find.return_value = mock.MagicMock(
            id=self.test_name
        )
        nova_client.aggregates.update.return_value = \
            mocked_updated_host_aggregate

        nova_client.aggregates.add_host = mock.MagicMock()
        nova_client.aggregates.remove_host = mock.MagicMock()
        nova_client.aggregates.set_metadata = mock.MagicMock()

        nova_client.get_id_from_resource.return_value = \
            self.existing_test_id
        nova_client.get_name_from_resource.return_value = \
            self.existing_test_name

        return nova_client

    def mock_ctx(self,
                 test_vars,
                 test_id,
                 test_deployment_id,
                 runtime_properties=None):

        ctx = MockContext()
        ctx.node = MockNodeContext(properties=test_vars)
        ctx.instance = MockNodeInstanceContext(
            id=test_id,
            runtime_properties=runtime_properties or {}
        )
        ctx.deployment = mock.Mock()
        ctx.deployment.id = test_deployment_id
        ctx.bootstrap_context = mock.Mock()
        setattr(ctx.bootstrap_context, 'resources_prefix', '')
        ctx.type = NODE_INSTANCE
        ctx.logger = mock.Mock()

        return ctx

    def test_add_hosts(self, *_):
        pass

    def test_set_metadata(self, *_):
        pass

    def test_remove_hosts(self, *_):
        pass

    @mock.patch(
        'openstack_plugin_common._put_client_in_kw',
        autospec=True,
        return_value=None
    )
    def test_create_and_delete(self, *_):
        # given
        test_vars_host1 = 'cf4301'
        test_vars_host2 = 'openstack-kilo-t2.novalocal'
        test_vars_hosts = [test_vars_host1, test_vars_host2]
        test_vars_metadata = {
            'test': 'value1'
        }
        test_vars = {
            'aggregate': {
                'name': self.test_name,
                'availability_zone': 'internal'
            },
            'hosts': test_vars_hosts,
            'metadata': test_vars_metadata,
            'resource_id': ''
        }

        ctx = self.mock_ctx(test_vars, self.test_id, self.test_deployment_id)
        nova_plugin.host_aggregate.ctx = ctx

        mocked_host_aggregate = self.MockHostAggregateOS(
            self.test_id,
            self.test_name
        )
        nova_client = self.mock_nova_client(mocked_host_aggregate)

        # when (create)
        nova_plugin.host_aggregate.create(nova_client, {})

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
            HOST_AGGREGATE_OPENSTACK_TYPE,
            ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY]
        )
        self.assertEqual(
            test_vars_hosts,
            ctx.instance.runtime_properties[HOSTS_PROPERTY]
        )
        nova_client.aggregates.add_host.assert_any_call(
            mocked_host_aggregate,
            test_vars_host1
        )
        nova_client.aggregates.add_host.assert_any_call(
            mocked_host_aggregate,
            test_vars_host2
        )
        nova_client.aggregates.set_metadata.assert_called_once_with(
            mocked_host_aggregate,
            test_vars_metadata
        )

        # when (delete)
        nova_plugin.host_aggregate.delete(nova_client)

        # then (delete)
        nova_client.aggregates.remove_host.assert_any_call(
            self.test_id,
            test_vars_host1
        )
        nova_client.aggregates.remove_host.assert_any_call(
            self.test_id,
            test_vars_host2
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
        'openstack_plugin_common._put_client_in_kw',
        autospec=True,
        return_value=None
    )
    @mock.patch(
        'openstack_plugin_common.get_resource_by_name_or_id',
        autospec=True,
        return_value=MockHostAggregateOS(
            existing_test_id,
            existing_test_name
        )
    )
    def test_create_and_delete_external_resource(self, *_):
        # given
        test_vars = {
            'aggregate': {},
            'resource_id': self.existing_test_id,
            'use_external_resource': True
        }

        ctx = self.mock_ctx(test_vars, self.test_id, self.test_deployment_id)
        nova_plugin.host_aggregate.ctx = ctx
        nova_client = self.mock_nova_client(None)

        # when (create)
        nova_plugin.host_aggregate.create(nova_client, {})

        # then (create)
        self.assertEqual(
            self.existing_test_name,
            ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY]
        )
        self.assertEqual(
            self.existing_test_id,
            ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY]
        )
        self.assertEqual(
            HOST_AGGREGATE_OPENSTACK_TYPE,
            ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY]
        )
        self.assertTrue(
            ctx.instance.runtime_properties[OPENSTACK_RESOURCE_PROPERTY]
        )
        nova_client.aggregates.create.assert_not_called()
        nova_client.aggregates.add_host.assert_not_called()
        nova_client.aggregates.set_metadata.assert_not_called()

        # when (delete)
        nova_plugin.host_aggregate.delete(nova_client)

        # then (delete)
        nova_client.aggregates.remove_host.assert_not_called()
        nova_client.aggregates.delete.assert_not_called()

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
        'openstack_plugin_common._put_client_in_kw',
        autospec=True,
        return_value=None
    )
    def test_update(self, *_):
        # given
        test_vars_host1 = 'cf4301'
        test_vars_host2 = 'openstack-kilo-t2.novalocal'
        test_vars_host3 = 'new_host'
        test_vars_old_hosts = [test_vars_host1, test_vars_host2]
        test_vars_new_hosts = [test_vars_host3]
        test_vars_metadata = {
            'test': 'value1'
        }
        test_vars = {
            'aggregate': {
                'name': self.test_name,
                'availability_zone': 'internal'
            },
            'hosts': test_vars_old_hosts,
            'metadata': test_vars_metadata,
            'resource_id': ''
        }

        ctx = self.mock_ctx(
            test_vars,
            self.test_id,
            self.test_deployment_id,
            {
                OPENSTACK_ID_PROPERTY: self.test_id,
                OPENSTACK_NAME_PROPERTY: self.test_name,
                OPENSTACK_TYPE_PROPERTY: HOST_AGGREGATE_OPENSTACK_TYPE,
                HOSTS_PROPERTY: test_vars_old_hosts
            }
        )
        nova_plugin.host_aggregate.ctx = ctx

        mocked_host_aggregate = self.MockHostAggregateOS(
            self.test_id,
            self.test_name
        )

        mocked_updated_host_aggregate = \
            self.MockHostAggregateOS(self.test_id, self.updated_name)
        nova_client = self.mock_nova_client(
            mocked_host_aggregate,
            mocked_updated_host_aggregate
        )

        # when
        nova_plugin.host_aggregate.update(
            nova_client,
            {},
            hosts=test_vars_new_hosts
        )

        # then
        self.assertEqual(
            self.updated_name,
            ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY]
        )
        self.assertEqual(
            self.test_id,
            ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY]
        )
        self.assertEqual(
            HOST_AGGREGATE_OPENSTACK_TYPE,
            ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY]
        )
        self.assertEqual(
            test_vars_new_hosts,
            ctx.instance.runtime_properties[HOSTS_PROPERTY]
        )
        nova_client.aggregates.remove_host.assert_any_call(
            self.test_id,
            test_vars_host1
        )
        nova_client.aggregates.remove_host.assert_any_call(
            self.test_id,
            test_vars_host2
        )
        nova_client.aggregates.add_host.assert_any_call(
            mocked_updated_host_aggregate,
            test_vars_host3
        )
        nova_client.aggregates.set_metadata.assert_called_once_with(
            mocked_updated_host_aggregate,
            test_vars_metadata
        )

    @mock.patch(
        'openstack_plugin_common._put_client_in_kw',
        autospec=True,
        return_value=None
    )
    def test_list(self, *_):
        # given
        test_vars_host1 = 'cf4301'
        test_vars_host2 = 'openstack-kilo-t2.novalocal'
        test_vars_hosts = [test_vars_host1, test_vars_host2]
        test_vars_metadata = {
            'test': 'value1'
        }
        test_vars = {
            'aggregate': {
                'name': self.test_name,
                'availability_zone': 'internal'
            },
            'hosts': test_vars_hosts,
            'metadata': test_vars_metadata,
            'resource_id': ''
        }

        ctx = self.mock_ctx(
            test_vars,
            self.test_id,
            self.test_deployment_id,
            {
                OPENSTACK_ID_PROPERTY: self.test_id,
                OPENSTACK_NAME_PROPERTY: self.test_name,
                OPENSTACK_TYPE_PROPERTY: HOST_AGGREGATE_OPENSTACK_TYPE,
                HOSTS_PROPERTY: test_vars_hosts
            }
        )
        nova_plugin.host_aggregate.ctx = ctx

        mocked_host_aggregate = self.MockHostAggregateOS(
            self.test_id,
            self.test_name
        )
        nova_client = self.mock_nova_client(mocked_host_aggregate)

        # when
        nova_plugin.host_aggregate.list_host_aggregates(nova_client)

        # then
        ha_list_key = '{}_list'.format(HOST_AGGREGATE_OPENSTACK_TYPE)
        self.assertIn(ha_list_key, ctx.instance.runtime_properties)
        self.assertEqual(
            [{'name': self.test_name, 'id': self.test_id}],
            ctx.instance.runtime_properties[ha_list_key]
        )
