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
import openstack.compute.v2.keypair

# Local imports
from openstack_plugin.tests.base import OpenStackTestBase
from openstack_plugin.resources.compute import keypair
from openstack_plugin.constants import (RESOURCE_ID,
                                        OPENSTACK_NAME_PROPERTY,
                                        OPENSTACK_TYPE_PROPERTY,
                                        KEYPAIR_OPENSTACK_TYPE)


@mock.patch('openstack.connect')
class KeyPairTestCase(OpenStackTestBase):

    def setUp(self):
        super(KeyPairTestCase, self).setUp()

    @property
    def resource_config(self):
        return {
            'name': 'test_key_pair',
        }

    def test_create(self, mock_connection):
        # Prepare the context for create operation
        self._prepare_context_for_operation(
            test_name='KeyPairTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.create')

        keypair_instance = openstack.compute.v2.keypair.Keypair(**{
            'id': 'test_key_pair',
            'name': 'test_key_pair',
            'fingerprint': 'test_fingerprint',
            'public_key': 'test_public_key',
            'private_key': 'test_private_key',

        })
        # Mock keypair response
        mock_connection().compute.create_keypair = \
            mock.MagicMock(return_value=keypair_instance)
        # Call create keypair
        keypair.create(openstack_resource=None)

        self.assertEqual(self._ctx.instance.runtime_properties[RESOURCE_ID],
                         'test_key_pair')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY],
            'test_key_pair')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY],
            KEYPAIR_OPENSTACK_TYPE)

        self.assertEqual(
            self._ctx.instance.runtime_properties['public_key'],
            'test_public_key')

        self.assertEqual(
            self._ctx.instance.runtime_properties['private_key'],
            'test_private_key')

    def test_delete(self, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            test_name='KeyPairTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.delete')

        keypair_instance = openstack.compute.v2.keypair.Keypair(**{
            'id': 'test_key_pair',
            'name': 'test_key_pair',
            'fingerprint': 'test_fingerprint',
            'public_key': 'test_public_key',
            'private_key': 'test_private_key',

        })
        # Mock delete keypair response
        mock_connection().compute.delete_keypair = \
            mock.MagicMock(return_value=None)
        # Mock get keypair
        mock_connection().compute.get_keypair = \
            mock.MagicMock(return_value=keypair_instance)

        # Call delete keypair
        keypair.delete(openstack_resource=None)

        for attr in [RESOURCE_ID,
                     OPENSTACK_NAME_PROPERTY,
                     OPENSTACK_TYPE_PROPERTY,
                     'public_key',
                     'private_key']:
            self.assertNotIn(attr,
                             self._ctx.instance.runtime_properties)

    def test_list_keypairs(self, mock_connection):
        # Prepare the context for list keypairs operation
        self._prepare_context_for_operation(
            test_name='KeyPairTestCase',
            ctx_operation_name='cloudify.interfaces.operations.list')

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
        # Mock list keypairs
        mock_connection().compute.keypairs = \
            mock.MagicMock(return_value=keypair_list)

        # Mock find project response
        mock_connection().identity.find_project = \
            mock.MagicMock(return_value=self.project_resource)

        # Call list keypair
        keypair.list_keypairs(openstack_resource=None)

        # Check if the keypairs list saved as runtime properties
        self.assertIn(
            'key_pair_list',
            self._ctx.instance.runtime_properties)

        # Check the size of keypairs list
        self.assertEqual(
            len(self._ctx.instance.runtime_properties['key_pair_list']), 2)

    @mock.patch('openstack_sdk.common.OpenstackResource.get_quota_sets')
    def test_creation_validation(self, mock_quota_sets, mock_connection):
        # Prepare the context for creation validation keypairs operation
        self._prepare_context_for_operation(
            test_name='KeyPairTestCase',
            ctx_operation_name='cloudify.interfaces.validation.creation')

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
        # Mock list keypairs
        mock_connection().compute.keypairs = \
            mock.MagicMock(return_value=keypair_list)

        # Mock the quota size response
        mock_quota_sets.return_value = 20

        # Call creation validation
        keypair.creation_validation(openstack_resource=None)
