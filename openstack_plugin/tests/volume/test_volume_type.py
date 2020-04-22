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
import openstack.block_storage.v2.type

# Local imports
from openstack_plugin.tests.base import OpenStackTestBase
from openstack_plugin.resources.volume import volume_type
from openstack_plugin.constants import (RESOURCE_ID,
                                        OPENSTACK_NAME_PROPERTY,
                                        OPENSTACK_TYPE_PROPERTY,
                                        VOLUME_TYPE_OPENSTACK_TYPE)


@mock.patch('openstack.connect')
class VolumeTypeTestCase(OpenStackTestBase):

    def setUp(self):
        super(VolumeTypeTestCase, self).setUp()

    @property
    def resource_config(self):
        return {
            'name': 'test_volume_type',
            'extra_specs': {
                'capabilities': 'gpu',
            }
        }

    def test_create(self, mock_connection):
        # Prepare the context for create operation
        self._prepare_context_for_operation(
            test_name='VolumeTypeTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.create')

        volume_type_instance = openstack.block_storage.v2.type.Type(**{
            'id': '1',
            'name': 'test_volume_type',
            'extra_specs': {
                'capabilities': 'gpu',
            }
        })
        # Mock create volume type response
        mock_connection().block_storage.create_type = \
            mock.MagicMock(return_value=volume_type_instance)

        # Call create volume type
        volume_type.create(openstack_resource=None)

        self.assertEqual(self._ctx.instance.runtime_properties[RESOURCE_ID],
                         '1')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY],
            'test_volume_type')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY],
            VOLUME_TYPE_OPENSTACK_TYPE)

    def test_delete(self, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            test_name='VolumeTypeTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.delete')

        volume_type_instance = openstack.block_storage.v2.type.Type(**{
            'id': '1',
            'name': 'test_volume_type',
            'extra_specs': {
                'capabilities': 'gpu',
            }
        })
        # Mock get volume type response
        mock_connection().block_storage.get_type = \
            mock.MagicMock(return_value=volume_type_instance)

        # Mock delete volume type response
        mock_connection().block_storage.delete_type = \
            mock.MagicMock(return_value=None)

        # Call delete volume type
        volume_type.delete(openstack_resource=None)

        for attr in [RESOURCE_ID,
                     OPENSTACK_NAME_PROPERTY,
                     OPENSTACK_TYPE_PROPERTY]:
            self.assertNotIn(attr, self._ctx.instance.runtime_properties)
