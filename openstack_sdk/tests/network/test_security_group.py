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
import openstack.network.v2.security_group

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import networks


class SecurityGroupTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(SecurityGroupTestCase, self).setUp()

        self.fake_client =\
            self.generate_fake_openstack_connection('security_group')

        self.security_group_instance = networks.OpenstackSecurityGroup(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.security_group_instance.connection = self.connection

    def test_get_security_group(self):
        sg = openstack.network.v2.security_group.SecurityGroup(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_name',
            'created_at': '2016-10-04T12:14:57.233772',
            'description': '1',
            'revision_number': 3,
            'tenant_id': '4',
            'updated_at': '2016-10-14T12:16:57.233772',
            'tags': ['5']
        })
        self.security_group_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_security_group = mock.MagicMock(return_value=sg)

        response = self.security_group_instance.get()
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.name, 'test_name')

    def test_list_security_groups(self):
        sgs = [
            openstack.network.v2.security_group.SecurityGroup(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_name_1',
                'created_at': '2016-10-04T12:14:57.233772',
                'description': '1',
                'revision_number': 3,
                'tenant_id': '4',
                'updated_at': '2016-10-14T12:16:57.233772',
                'tags': ['5']

            }),
            openstack.network.v2.security_group.SecurityGroup(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': 'test_name_2',
                'created_at': '2016-10-04T12:14:57.233772',
                'description': '1',
                'revision_number': 3,
                'tenant_id': '4',
                'updated_at': '2016-10-14T12:16:57.233772',
                'tags': ['5']

            })
        ]

        self.fake_client.security_groups = mock.MagicMock(return_value=sgs)
        response = self.security_group_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_security_group(self):
        sg = {
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_name',
            'description': 'test_description',
            'availability_zone_hints': ['1'],
            'availability_zones': ['2'],
            'distributed': False,
            'flavor_id': '5',
            'ha': False,
            'routes': ['8'],
            'tenant_id': '10',
        }

        new_res = openstack.network.v2.security_group.SecurityGroup(**sg)
        self.security_group_instance.config = sg
        self.fake_client.create_security_group =\
            mock.MagicMock(return_value=new_res)

        response = self.security_group_instance.create()
        self.assertEqual(response.name, sg['name'])
        self.assertEqual(response.description, sg['description'])

    def test_update_security_group(self):
        old_sg = openstack.network.v2.security_group.SecurityGroup(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_name',
            'created_at': '2016-10-04T12:14:57.233772',
            'description': '1',
            'revision_number': 3,
            'tenant_id': '4',
            'updated_at': '2016-10-14T12:16:57.233772',
            'tags': ['5']

        })

        new_config = {
            'name': 'test_name_update',
            'description': 'test_description_update',
        }

        new_sg = openstack.network.v2.security_group.SecurityGroup(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_name_update',
            'description': 'test_description_update',
            'created_at': '2016-10-04T12:14:57.233772',
            'revision_number': 3,
            'tenant_id': '4',
            'updated_at': '2016-10-14T12:16:57.233772',
            'tags': ['5']

        })

        self.security_group_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_security_group =\
            mock.MagicMock(return_value=old_sg)
        self.fake_client.update_security_group =\
            mock.MagicMock(return_value=new_sg)

        response = self.security_group_instance.update(new_config=new_config)
        self.assertNotEqual(response.name, old_sg.name)
        self.assertNotEqual(response.description, old_sg.description)

    def test_delete_security_group(self):
        sg = openstack.network.v2.security_group.SecurityGroup(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_name',
            'created_at': '2016-10-04T12:14:57.233772',
            'description': '1',
            'revision_number': 3,
            'tenant_id': '4',
            'updated_at': '2016-10-14T12:16:57.233772',
            'tags': ['5']

        })

        self.security_group_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_security_group = mock.MagicMock(return_value=sg)
        self.fake_client.delete_security_group = \
            mock.MagicMock(return_value=None)

        response = self.security_group_instance.delete()
        self.assertIsNone(response)
