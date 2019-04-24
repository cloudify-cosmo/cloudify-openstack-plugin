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
import openstack.network.v2.rbac_policy

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import networks


class RBACPolicyTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(RBACPolicyTestCase, self).setUp()

        self.fake_client = \
            self.generate_fake_openstack_connection('rbac_policy')

        self.rbac_policy_instance = networks.OpenstackRBACPolicy(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.rbac_policy_instance.connection = self.connection

    def test_get_rbac_policy(self):
        sg = openstack.network.v2.rbac_policy.RBACPolicy(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': None,
            'target_project_id': 'test_target_project_id',
            'object_type': 'test_object_type',
            'object_id': 3,
            'location': None,
            'action': 'test_action',
            'project_id': 4
        })
        self.rbac_policy_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_rbac_policy = mock.MagicMock(return_value=sg)

        response = self.rbac_policy_instance.get()
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.target_project_id, 'test_target_project_id')

    def test_list_rbac_policies(self):
        policies = [
            openstack.network.v2.rbac_policy.RBACPolicy(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': None,
                'target_project_id': 'test_target_project_id_1',
                'object_type': 'test_object_type_1',
                'object_id': 3,
                'action': 'test_action_1',
                'project_id': 4

            }),
            openstack.network.v2.rbac_policy.RBACPolicy(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': None,
                'target_project_id': 'test_target_project_id_2',
                'object_type': 'test_object_type_2',
                'object_id': 4,
                'action': 'test_action_2',
                'project_id': 5,
            })
        ]

        self.fake_client.rbac_policies = \
            mock.MagicMock(return_value=policies)
        response = self.rbac_policy_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_rbac_policy(self):
        policy = \
            {
                'target_tenant': 'test_target_tenant',
                'object_type': 'test_object_type',
                'object_id': 1,
                'action': 'test_action',
            }

        new_res = openstack.network.v2.rbac_policy.RBACPolicy(**policy)
        self.rbac_policy_instance.config = policy
        self.fake_client.create_rbac_policy = \
            mock.MagicMock(return_value=new_res)

        response = self.rbac_policy_instance.create()
        self.assertEqual(response.object_id, policy['object_id'])
        self.assertEqual(response.object_type, policy['object_type'])

    def test_update_rbac_policy(self):
        old_policy = openstack.network.v2.rbac_policy.RBACPolicy(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'target_tenant': 'test_target_tenant',
            'object_type': 'test_object_type',
            'object_id': 1,
            'action': 'test_action',
        })

        new_config = {
            'target_tenant': 'test_target_tenant_update',
        }

        new_policy = openstack.network.v2.rbac_policy.RBACPolicy(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': None,
            'target_project_id': 'test_target_tenant_update',
            'object_type': 'test_object_type',
            'object_id': 3,
            'location': None,
            'action': 'test_action',
            'project_id': 3,

        })

        self.rbac_policy_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_rbac_policy = \
            mock.MagicMock(return_value=old_policy)
        self.fake_client.update_rbac_policy =\
            mock.MagicMock(return_value=new_policy)

        response = self.rbac_policy_instance.update(new_config=new_config)
        self.assertNotEqual(response.target_project_id,
                            old_policy.target_project_id)

    def test_delete_security_group(self):
        policy = openstack.network.v2.rbac_policy.RBACPolicy(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': None,
            'target_project_id': 'test_target_project_id_1',
            'object_type': 'test_object_type_1',
            'object_id': 3,
            'location': None,
            'action': 'test_action_1',
            'project_id': 4

        }),

        self.rbac_policy_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_rbac_policy = mock.MagicMock(return_value=policy)
        self.fake_client.delete_rbac_policy = mock.MagicMock(return_value=None)

        response = self.rbac_policy_instance.delete()
        self.assertIsNone(response)
