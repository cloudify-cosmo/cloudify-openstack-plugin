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
import openstack.dns.v2.recordset

# Local imports
from openstack_plugin.tests.base import OpenStackTestBase
from openstack_plugin.resources.dns_service import record_set
from openstack_plugin.constants import (RESOURCE_ID,
                                        OPENSTACK_NAME_PROPERTY,
                                        OPENSTACK_TYPE_PROPERTY)


@mock.patch('openstack.connect')
class RecordSetTestCase(OpenStackTestBase):

    def setUp(self):
        super(RecordSetTestCase, self).setUp()

    @property
    def resource_config(self):
        return {
            'name': 'test_recordset',
        }

    def test_create(self, mock_connection):
        # Prepare the context for create operation
        self._prepare_context_for_operation(
            test_name='RecordSetTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.create')

        recordset_instance = openstack.dns.v2.recordset.Recordset(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_recordset',
            'ttl': 7200,
            'records': ['192.168.1.1', '192.168.2.1'],
            'type': 'A',
            'zone_id': '388814ef-3c5d-415e-a866-5b1d13d78dae',

        })
        # Mock recordset response
        mock_connection().dns.create_recordset = \
            mock.MagicMock(return_value=recordset_instance)

        # Call create recordset
        record_set.create()

        self.assertEqual(self._ctx.instance.runtime_properties[RESOURCE_ID],
                         'a95b5509-c122-4c2f-823e-884bb559afe8')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY],
            'test_recordset')

    def test_delete(self, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            test_name='RecordSetTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.delete')

        recordset_instance = openstack.dns.v2.recordset.Recordset(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_recordset',
            'ttl': 7200,
            'records': ['192.168.1.1', '192.168.2.1'],
            'type': 'A',
            'zone_id': '388814ef-3c5d-415e-a866-5b1d13d78dae',

        })
        self._ctx.instance.runtime_properties[RESOURCE_ID] = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        # Mock delete recordset response
        mock_connection().dns.delete_recordset = \
            mock.MagicMock(return_value=recordset_instance)

        # Mock get recordset response
        mock_connection().dns.get_recordset = \
            mock.MagicMock(return_value=recordset_instance)

        # Call delete recordset
        record_set.delete()

        for attr in [RESOURCE_ID,
                     OPENSTACK_NAME_PROPERTY,
                     OPENSTACK_TYPE_PROPERTY]:
            self.assertNotIn(attr,
                             self._ctx.instance.runtime_properties)
