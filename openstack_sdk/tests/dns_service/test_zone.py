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

# Standard imports
import mock

# Third party imports
import openstack.dns.v2.zone

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import dns_service


class ZoneTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(ZoneTestCase, self).setUp()
        self.fake_client = self.generate_fake_openstack_connection('dns')
        self.zone_instance = dns_service.OpenstackZone(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.zone_instance.connection = self.connection

    def test_get_zone(self):
        zone = openstack.dns.v2.zone.Zone(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'my_zone',
            'ttl': 7200,
            'email': 'my_zone@test.com',

        })
        self.zone_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.find_zone = mock.MagicMock(return_value=zone)

        response = self.zone_instance.get()
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.ttl, 7200)
        self.assertEqual(response.name, 'my_zone')

    def test_create_zone(self):
        zone = {
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'my_zone',
            'ttl': 7200,
            'email': 'my_zone@test.com',
        }

        new_res = openstack.dns.v2.zone.Zone(**zone)
        self.zone_instance.config = zone
        self.fake_client.create_zone = \
            mock.MagicMock(return_value=new_res)

        response = self.zone_instance.create()
        self.assertEqual(response.id, zone['id'])
        self.assertEqual(response.name, zone['name'])

    def test_delete_zone(self):
        zone = openstack.dns.v2.zone.Zone(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'my_zone',
            'ttl': 7200,
            'email': 'my_zone@test.com',
        })

        self.zone_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_zone = mock.MagicMock(return_value=zone)
        self.fake_client.delete_zone = mock.MagicMock(return_value=None)

        response = self.zone_instance.delete()
        self.assertIsNone(response)
