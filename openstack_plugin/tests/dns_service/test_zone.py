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
import openstack.dns.v2.zone

# Local imports
from openstack_plugin.tests.base import OpenStackTestBase
from openstack_plugin.resources.dns_service import zone
from openstack_plugin.constants import (RESOURCE_ID,
                                        OPENSTACK_NAME_PROPERTY,
                                        OPENSTACK_TYPE_PROPERTY)


@mock.patch('openstack.connect')
class ZoneTestCase(OpenStackTestBase):

    def setUp(self):
        super(ZoneTestCase, self).setUp()

    @property
    def resource_config(self):
        return {
            'name': 'test_zone',
        }

    def test_create(self, mock_connection):
        # Prepare the context for create operation
        self._prepare_context_for_operation(
            test_name='ZoneTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.create')

        zone_instance = openstack.dns.v2.zone.Zone(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_zone',
            'ttl': 7200,
            'email': 'my_zone@test.com',

        })
        # Mock zone response
        mock_connection().dns.create_zone = \
            mock.MagicMock(return_value=zone_instance)

        # Call create zone
        zone.create(openstack_resource=None)

        self.assertEqual(self._ctx.instance.runtime_properties[RESOURCE_ID],
                         'a95b5509-c122-4c2f-823e-884bb559afe8')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY],
            'test_zone')

    def test_delete(self, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            test_name='ZoneTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.delete')

        zone_instance = openstack.dns.v2.zone.Zone(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_zone',
            'ttl': 7200,
            'email': 'my_zone@test.com',

        })
        self._ctx.instance.runtime_properties[RESOURCE_ID] = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        # Mock delete zone response
        mock_connection().dns.delete_zone = \
            mock.MagicMock(return_value=zone_instance)

        # Mock get zone response
        mock_connection().dns.get_zone = \
            mock.MagicMock(return_value=zone_instance)

        # Call delete zone
        zone.delete(openstack_resource=None)

        for attr in [RESOURCE_ID,
                     OPENSTACK_NAME_PROPERTY,
                     OPENSTACK_TYPE_PROPERTY]:
            self.assertNotIn(attr,
                             self._ctx.instance.runtime_properties)
