# #######
# Copyright (c) 2019 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Third party imports
import mock
import openstack.compute.v2.aggregate
from cloudify.exceptions import NonRecoverableError

# Local imports
from openstack_plugin.tests.base import OpenStackTestBase
from openstack_plugin.resources.compute import host_aggregate
from openstack_plugin.constants import (RESOURCE_ID,
                                        OPENSTACK_NAME_PROPERTY,
                                        OPENSTACK_TYPE_PROPERTY,
                                        HOST_AGGREGATE_OPENSTACK_TYPE)


@mock.patch('openstack.connect')
class HostAggregateTestCase(OpenStackTestBase):

    def setUp(self):
        super(HostAggregateTestCase, self).setUp()

    @property
    def resource_config(self):
        return {
            'name': 'test_host_aggregate',
            'description': 'host_aggregate_description'
        }

    @property
    def node_properties(self):
        properties = super(HostAggregateTestCase, self).node_properties
        properties['metadata'] = {'key-1': 'test-1', 'key-2': 'test-2'}
        properties['hosts'] = ['host-1', 'host-2']
        return properties

    def test_create(self, mock_connection):
        # Prepare the context for create operation
        self._prepare_context_for_operation(
            test_name='HostAggregateTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.create')

        aggregate_instance = openstack.compute.v2.aggregate.Aggregate(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_host_aggregate',
            'availability_zone': 'test_availability_zone',
        })
        # Mock aggregate response
        mock_connection().compute.create_aggregate = \
            mock.MagicMock(return_value=aggregate_instance)

        # Call create aggregate
        host_aggregate.create()

        self.assertEqual(self._ctx.instance.runtime_properties[RESOURCE_ID],
                         'a95b5509-c122-4c2f-823e-884bb559afe8')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY],
            'test_host_aggregate')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY],
            HOST_AGGREGATE_OPENSTACK_TYPE)

    def test_configure(self, mock_connection):
        # Prepare the context for configure operation
        self._prepare_context_for_operation(
            test_name='HostAggregateTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.configure')
        hosts_to_add = ['host-1', 'host-2']
        old_aggregate_instance = openstack.compute.v2.aggregate.Aggregate(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_host_aggregate',
            'availability_zone': 'test_availability_zone',
        })

        aggregate_with_metadata_ = openstack.compute.v2.aggregate.Aggregate(**{
            'id': '1',
            'name': 'test_host_aggregate',
            'availability_zone': 'test_availability_zone',
            'metadata': {
                'key-1': 'test-1',
                'key-2': 'test-2'
            }
        })

        aggregate_with_hosts = openstack.compute.v2.aggregate.Aggregate(**{
            'id': '1',
            'name': 'test_host_aggregate',
            'availability_zone': 'test_availability_zone',
            'metadata': {
                'key-1': 'test-1',
                'key-2': 'test-2'
            },
            'hosts': hosts_to_add
        })

        self._ctx.instance.runtime_properties[RESOURCE_ID] = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'

        # Mock get aggregate response
        mock_connection().compute.get_aggregate = \
            mock.MagicMock(return_value=old_aggregate_instance)

        # Mock aggregate response
        mock_connection().compute.set_aggregate_metadata = \
            mock.MagicMock(return_value=aggregate_with_metadata_)

        # Mock add host aggregate response
        mock_connection().compute.add_host_to_aggregate = \
            mock.MagicMock(return_value=aggregate_with_hosts)

        # Call configure aggregate
        host_aggregate.configure()

        self.assertEqual(
            len(self._ctx.instance.runtime_properties['hosts']), 2)

    def test_update(self, _):
        # Prepare the context for update operation
        self._prepare_context_for_operation(
            test_name='FlavorTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.update')

        updated_config = {
            'name': 'Updated Name'
        }

        with self.assertRaises(NonRecoverableError):
            # Call update aggregate
            host_aggregate.update(args=updated_config)

    def test_delete(self, mock_connection):
        # Prepare the context for configure operation
        self._prepare_context_for_operation(
            test_name='HostAggregateTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.delete',
            test_runtime_properties={
                'hosts': ['host-1']
            })
        old_aggregate_instance = openstack.compute.v2.aggregate.Aggregate(**{
            'id': '1',
            'name': 'test_host_aggregate',
            'availability_zone': 'test_availability_zone',
            'metadata': {
                'key-1': 'test-1',
                'key-2': 'test-2'
            },
            'hosts': ['host-1', 'host-2']
        })

        updated_aggregate_instance = \
            openstack.compute.v2.aggregate.Aggregate(**{
                'id': '1',
                'name': 'test_host_aggregate',
                'availability_zone': 'test_availability_zone',
                'metadata': {
                    'key-1': 'test-1',
                    'key-2': 'test-2'
                },
                'hosts': ['host-2']
            })

        self._ctx.instance.runtime_properties[RESOURCE_ID] = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'

        # Mock get aggregate response
        mock_connection().compute.get_aggregate = \
            mock.MagicMock(side_effect=[old_aggregate_instance,
                                        updated_aggregate_instance])

        # Mock remove host aggregate response
        mock_connection().compute.remove_host_from_aggregate = \
            mock.MagicMock(return_value=updated_aggregate_instance)

        # Mock aggregate response
        mock_connection().compute.delete_aggregate = \
            mock.MagicMock(return_value=None)

        # Call delete aggregate
        host_aggregate.delete()

        for attr in [RESOURCE_ID,
                     OPENSTACK_NAME_PROPERTY,
                     OPENSTACK_TYPE_PROPERTY,
                     'hosts']:
            self.assertNotIn(attr,
                             self._ctx.instance.runtime_properties)

    def test_list_aggregates(self,
                             mock_connection):
        # Prepare the context for list aggregates operation
        self._prepare_context_for_operation(
            test_name='HostAggregateTestCase',
            ctx_operation_name='cloudify.interfaces.operations.list')

        aggregate_list = [
            openstack.compute.v2.aggregate.Aggregate(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_aggregate_1',
                'availability_zone': 'test_availability_zone_1',
            }),
            openstack.compute.v2.aggregate.Aggregate(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': 'test_aggregate_2',
                'availability_zone': 'test_availability_zone_2',
            }),
        ]

        # Mock list aggregate response
        mock_connection().compute.aggregates = \
            mock.MagicMock(return_value=aggregate_list)

        # Mock find project response
        mock_connection().identity.find_project = \
            mock.MagicMock(return_value=self.project_resource)

        # Call list aggregates
        host_aggregate.list_aggregates()

        # Check if the aggregates list saved as runtime properties
        self.assertIn(
            'aggregate_list',
            self._ctx.instance.runtime_properties)

        # Check the size of aggregate list
        self.assertEqual(
            len(self._ctx.instance.runtime_properties['aggregate_list']), 2)

    def test_add_hosts(self, mock_connection):
        # Prepare the context for add hosts operation
        self._prepare_context_for_operation(
            test_name='HostAggregateTestCase',
            ctx_operation_name='cloudify.interfaces.operations.add_hosts')

        hosts_to_add = ['host-1', 'host-2']
        old_aggregate_instance = openstack.compute.v2.aggregate.Aggregate(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_host_aggregate',
            'availability_zone': 'test_availability_zone',
        })

        new_aggregate_instance = openstack.compute.v2.aggregate.Aggregate(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_host_aggregate',
            'availability_zone': 'test_availability_zone',
            'hosts': hosts_to_add
        })

        self._ctx.instance.runtime_properties[RESOURCE_ID] = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'

        # Mock get aggregate response
        mock_connection().compute.get_aggregate = \
            mock.MagicMock(return_value=old_aggregate_instance)

        # Mock add host aggregate response
        mock_connection().compute.add_host_to_aggregate = \
            mock.MagicMock(return_value=new_aggregate_instance)

        # Call add hosts to aggregate
        host_aggregate.add_hosts(hosts=hosts_to_add)

    def test_add_invalid_hosts(self, _):
        # Prepare the context for add hosts operation
        self._prepare_context_for_operation(
            test_name='HostAggregateTestCase',
            ctx_operation_name='cloudify.interfaces.operations.add_hosts')

        invalid_hosts_to_add = 'invalid data'
        with self.assertRaises(NonRecoverableError):
            # Call add hosts to aggregate
            host_aggregate.add_hosts(hosts=invalid_hosts_to_add)

    def test_remove_hosts(self, mock_connection):
        # Prepare the context for remove hosts operation
        self._prepare_context_for_operation(
            test_name='HostAggregateTestCase',
            ctx_operation_name='cloudify.interfaces.operations.remove_hosts',
            test_runtime_properties={
                'hosts': ['host-1', 'host-2']
            })

        hosts_to_remove = ['host-1']
        old_aggregate_instance = openstack.compute.v2.aggregate.Aggregate(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_host_aggregate',
            'availability_zone': 'test_availability_zone',
            'hosts': ['host-1', 'host-2']
        })

        new_aggregate_instance = openstack.compute.v2.aggregate.Aggregate(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_host_aggregate',
            'availability_zone': 'test_availability_zone',
            'hosts': ['host-2']
        })
        self._ctx.instance.runtime_properties[RESOURCE_ID] = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'

        # Mock get aggregate response
        mock_connection().compute.get_aggregate = \
            mock.MagicMock(return_value=old_aggregate_instance)

        # Mock remove host aggregate response
        mock_connection().compute.remove_host_from_aggregate = \
            mock.MagicMock(return_value=new_aggregate_instance)

        # Call remove hosts from aggregate
        host_aggregate.remove_hosts(hosts=hosts_to_remove)

        self.assertEqual(
            len(self._ctx.instance.runtime_properties['hosts']), 1)

    def test_remove_invalid_hosts(self, _):
        # Prepare the context for remove hosts operation
        self._prepare_context_for_operation(
            test_name='HostAggregateTestCase',
            ctx_operation_name='cloudify.interfaces.operations.remove_hosts')

        invalid_hosts_to_remove = 'invalid data'
        with self.assertRaises(NonRecoverableError):
            # Call add hosts to aggregate
            host_aggregate.remove_hosts(hosts=invalid_hosts_to_remove)
