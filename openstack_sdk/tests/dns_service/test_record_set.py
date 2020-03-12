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
import openstack.dns.v2.recordset

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import dns_service


class RecordSetTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(RecordSetTestCase, self).setUp()
        self.fake_client = self.generate_fake_openstack_connection('dns')
        self.recordset_instance = dns_service.OpenstackRecordSet(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.recordset_instance.connection = self.connection

    def test_get_recordset(self):
        recordset = openstack.dns.v2.recordset.Recordset(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'my_record',
            'ttl': 7200,
            'records': ['192.168.1.1', '192.168.2.1'],
            'type': 'A',
            'zone_id': '388814ef-3c5d-415e-a866-5b1d13d78dae',

        })
        self.recordset_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.find_recordset = \
            mock.MagicMock(return_value=recordset)

        response = self.recordset_instance.get()
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.ttl, 7200)
        self.assertEqual(response.name, 'my_record')

    def test_create_recordset(self):
        recordset = {
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'my_record',
            'ttl': 7200,
            'records': ['192.168.1.1', '192.168.2.1'],
            'type': 'A',
            'zone_id': '388814ef-3c5d-415e-a866-5b1d13d78dae',

        }

        new_res = openstack.dns.v2.recordset.Recordset(**recordset)
        self.recordset_instance.config = recordset
        self.fake_client.create_recordset = \
            mock.MagicMock(return_value=new_res)

        response = self.recordset_instance.create()
        self.assertEqual(response.id, recordset['id'])
        self.assertEqual(response.name, recordset['name'])

    def test_delete_recordset(self):
        recordset = openstack.dns.v2.recordset.Recordset(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'my_record',
            'ttl': 7200,
            'records': ['192.168.1.1', '192.168.2.1'],
            'type': 'A',
            'zone_id': '388814ef-3c5d-415e-a866-5b1d13d78dae',

        })

        self.recordset_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_recordset = mock.MagicMock(return_value=recordset)
        self.fake_client.delete_recordset = mock.MagicMock(return_value=None)

        response = self.recordset_instance.delete()
        self.assertIsNone(response)
