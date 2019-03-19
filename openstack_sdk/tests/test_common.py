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
import unittest
import mock

# Third part imports
import openstack.compute.v2.server

# Local imports
from openstack_sdk.resources import get_server_password
from openstack_sdk.common import OpenstackResource


@mock.patch('openstack.connect')
class OpenStackCommonBase(unittest.TestCase):

    def setUp(self):
        super(OpenStackCommonBase, self).setUp()

    @mock.patch('openstack.proxy.Proxy')
    def test_get_server(self, mock_proxy, _):
        server = openstack.compute.v2.server.Server(**{
            'id': 'a34b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {'region': '3'},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',

        })
        server.get_password = mock.MagicMock(return_value='884bb559afe8')
        mock_proxy._get_resource = mock.MagicMock(return_value=server)
        password = get_server_password(mock_proxy, server)
        self.assertEqual(password, '884bb559afe8')

    def test_openstack_resource_instance(self, _):
        resource = OpenstackResource(
            client_config={'foo': 'foo', 'bar': 'bar'},
            resource_config={'name': 'foo-name',
                             'id': 'a95b5509-c122-4c2f-823e-884bb559afe9'}
        )

        self.assertEqual(resource.resource_id,
                         'a95b5509-c122-4c2f-823e-884bb559afe9')
        self.assertEqual(resource.name, 'foo-name')

    def test_valid_resource_id(self, _):
        resource = OpenstackResource(
            client_config={'foo': 'foo', 'bar': 'bar'},
            resource_config={'name': 'foo-name',
                             'id': 'a95b5509-c122-4c2f-823e-884bb559afe9'}
        )

        self.assertIsNone(resource.validate_resource_identifier())

    def test_invalid_resource_id(self, _):
        resource = OpenstackResource(
            client_config={'foo': 'foo', 'bar': 'bar'},
            resource_config={'name': 'foo-name',
                             'id': 'sad'}
        )

        self.assertIsNotNone(resource.validate_resource_identifier())

    @mock.patch('openstack_sdk.common.OpenstackResource.get_quota_sets')
    def test_get_quota_sets(self, mock_quota, _):
        resource = OpenstackResource(
            client_config={'foo': 'foo', 'bar': 'bar', 'project_name': 'test'},
            resource_config={'name': 'foo-name',
                             'id': 'a95b5509-c122-4c2f-823e-884bb559afe9'}
        )

        mock_quota.return_value = 15
        self.assertEqual(resource.get_quota_sets('test'), 15)

    def test_resource_plural(self, _):
        resource = OpenstackResource(
            client_config={'foo': 'foo', 'bar': 'bar'},
            resource_config={'name': 'foo-name',
                             'id': 'a95b5509-c122-4c2f-823e-884bb559afe9'}
        )

        self.assertEqual(resource.resource_plural('test'), 'tests')

    def test_create(self, _):
        resource = OpenstackResource(
            client_config={'foo': 'foo', 'bar': 'bar'},
            resource_config={'name': 'foo-name',
                             'id': 'a95b5509-c122-4c2f-823e-884bb559afe9'}
        )
        with self.assertRaises(NotImplementedError):
            resource.create()

    def test_delete(self, _):
        resource = OpenstackResource(
            client_config={'foo': 'foo', 'bar': 'bar'},
            resource_config={'name': 'foo-name',
                             'id': 'a95b5509-c122-4c2f-823e-884bb559afe9'}
        )
        with self.assertRaises(NotImplementedError):
            resource.delete()

    def test_get(self, _):
        resource = OpenstackResource(
            client_config={'foo': 'foo', 'bar': 'bar'},
            resource_config={'name': 'foo-name',
                             'id': 'a95b5509-c122-4c2f-823e-884bb559afe9'}
        )
        with self.assertRaises(NotImplementedError):
            resource.get()

    def test_list(self, _):
        resource = OpenstackResource(
            client_config={'foo': 'foo', 'bar': 'bar'},
            resource_config={'name': 'foo-name',
                             'id': 'a95b5509-c122-4c2f-823e-884bb559afe9'}
        )
        with self.assertRaises(NotImplementedError):
            resource.list()
