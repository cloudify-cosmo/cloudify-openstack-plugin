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
import openstack.compute.v2.flavor
from cloudify.exceptions import NonRecoverableError

# Local imports
from openstack_plugin.tests.base import OpenStackTestBase
from openstack_plugin.resources.compute import flavor
from openstack_plugin.constants import (RESOURCE_ID,
                                        OPENSTACK_NAME_PROPERTY,
                                        OPENSTACK_TYPE_PROPERTY,
                                        FLAVOR_OPENSTACK_TYPE)


@mock.patch('openstack.connect')
class KeyPairTestCase(OpenStackTestBase):

    def setUp(self):
        super(KeyPairTestCase, self).setUp()

    @property
    def resource_config(self):
        return {
            'name': 'test_flavor',
        }

    def test_create(self, mock_connection):
        # Prepare the context for create operation
        self._prepare_context_for_operation(
            test_name='FlavorTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.create')

        flavor_instance = openstack.compute.v2.flavor.Flavor(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_flavor',
            'links': '2',
            'os-flavor-access:is_public': True,
            'ram': 6,
            'vcpus': 8,
            'swap': 8

        })
        # Mock flavor response
        mock_connection().compute.create_flavor = \
            mock.MagicMock(return_value=flavor_instance)

        # Call create flavor
        flavor.create()

        self.assertEqual(self._ctx.instance.runtime_properties[RESOURCE_ID],
                         'a95b5509-c122-4c2f-823e-884bb559afe8')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY],
            'test_flavor')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY],
            FLAVOR_OPENSTACK_TYPE)

    def test_delete(self, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            test_name='FlavorTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.delete')

        flavor_instance = openstack.compute.v2.flavor.Flavor(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_flavor',
            'links': '2',
            'os-flavor-access:is_public': True,
            'ram': 6,
            'vcpus': 8,
            'swap': 8

        })
        # Mock delete flavor response
        mock_connection().compute.delete_flavor = \
            mock.MagicMock(return_value=flavor_instance)

        # Mock get flavor response
        mock_connection().compute.get_flavor = \
            mock.MagicMock(return_value=flavor_instance)

        # Call delete flavor
        flavor.delete()

        for attr in [RESOURCE_ID,
                     OPENSTACK_NAME_PROPERTY,
                     OPENSTACK_TYPE_PROPERTY]:
            self.assertNotIn(attr,
                             self._ctx.instance.runtime_properties)

    def test_update(self, _):
        # Prepare the context for update operation
        self._prepare_context_for_operation(
            test_name='FlavorTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.update')

        updated_config = {
            'name': 'Updated Name'
        }

        with self.assertRaises(NonRecoverableError):
            # Call update flavor
            flavor.update(args=updated_config)

    def test_list_flavors(self, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            test_name='FlavorTestCase',
            ctx_operation_name='cloudify.interfaces.operations.list')

        flavors = [
            openstack.compute.v2.flavor.FlavorDetail(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_flavor_1',
                'links': '2',
                'os-flavor-access:is_public': True,
                'ram': 6,
                'vcpus': 8,
                'swap': 8
            }),
            openstack.compute.v2.flavor.FlavorDetail(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': 'test_flavor_2',
                'links': '3',
                'os-flavor-access:is_public': True,
                'ram': 4,
                'vcpus': 3,
                'swap': 3
            })
        ]
        # Mock list flavors response
        mock_connection().compute.flavors = \
            mock.MagicMock(return_value=flavors)

        # Mock find project response
        mock_connection().identity.find_project = \
            mock.MagicMock(return_value=self.project_resource)

        flavor.list_flavors()

        # Check if the flavor list saved as runtime properties
        self.assertIn(
            'flavor_list',
            self._ctx.instance.runtime_properties)

        # Check the size of flavor list
        self.assertEqual(
            len(self._ctx.instance.runtime_properties['flavor_list']), 2)
