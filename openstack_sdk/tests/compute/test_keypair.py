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
import openstack.compute.v2.keypair

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import compute


class KeyPairTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(KeyPairTestCase, self).setUp()
        self.fake_client = self.generate_fake_openstack_connection('key_pair')
        self.keypair_instance = compute.OpenstackKeyPair(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.keypair_instance.connection = self.connection

    def test_get_keypair(self):
        keypair = openstack.compute.v2.keypair.Keypair(**{
            'name': 'test_key_pair',
            'fingerprint': 'test_fingerprint',
            'public_key': 'test_public_key'

        })
        self.keypair_instance.name = 'test_key_pair'
        self.fake_client.get_keypair = mock.MagicMock(return_value=keypair)

        response = self.keypair_instance.get()
        self.assertEqual(response.name, 'test_key_pair')
        self.assertEqual(response.fingerprint, 'test_fingerprint')
        self.assertEqual(response.public_key, 'test_public_key')

    def test_list_keypairs(self):
        keypair_list = [
            openstack.compute.v2.keypair.Keypair(**{
                'name': 'test_key_pair_1',
                'fingerprint': 'test_fingerprint_1',
                'public_key': 'test_public_key_1'
            }),
            openstack.compute.v2.keypair.Keypair(**{
                'name': 'test_key_pair_2',
                'fingerprint': 'test_fingerprint_2',
                'public_key': 'test_public_key_2'
            }),
        ]

        self.fake_client.keypairs = mock.MagicMock(return_value=keypair_list)

        response = self.keypair_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_keypair(self):
        config = {
            'name': 'test_key_pair',
        }

        keypair = {
            'name': 'test_key_pair',
            'fingerprint': 'test_fingerprint_1',
            'public_key': 'test_public_key_1',
            'private_key': 'test_private_key_1'
        }

        self.keypair_instance.config = config
        new_res = openstack.compute.v2.keypair.Keypair(**keypair)
        self.fake_client.create_keypair = mock.MagicMock(return_value=new_res)

        response = self.keypair_instance.create()
        self.assertEqual(response.name, config['name'])

    def test_delete_flavor(self):
        keypair = openstack.compute.v2.keypair.Keypair(**{
            'name': 'test_key_pair',
            'fingerprint': 'test_fingerprint',
            'public_key': 'test_public_key'

        })

        self.keypair_instance.resource_id = '2'
        self.fake_client.get_keypair = mock.MagicMock(return_value=keypair)
        self.fake_client.delete_keypair = mock.MagicMock(return_value=None)

        response = self.keypair_instance.delete()
        self.assertIsNone(response)
