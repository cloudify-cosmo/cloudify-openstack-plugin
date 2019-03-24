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
import openstack.identity.v3.project

# Local imports
from openstack_sdk.tests import base
from openstack_sdk.resources import identity


class UserTestCase(base.OpenStackSDKTestBase):
    def setUp(self):
        super(UserTestCase, self).setUp()
        self.fake_client = self.generate_fake_openstack_connection('project')
        self.project_instance = identity.OpenstackProject(
            client_config=self.client_config,
            logger=mock.MagicMock()
        )
        self.project_instance.connection = self.connection

    def test_get_project(self):
        project = openstack.identity.v3.project.Project(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_project',
            'description': 'Testing Project',
            'domain_id': 'test_domain_id',
            'enabled': True,
            'is_domain': True,
            'links': ['test1', 'test2'],
            'parent_id': 'test_parent_id'

        })
        self.project_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_project = mock.MagicMock(return_value=project)

        response = self.project_instance.get()
        self.assertEqual(response.id, 'a95b5509-c122-4c2f-823e-884bb559afe8')
        self.assertEqual(response.name, 'test_project')
        self.assertEqual(response.domain_id, 'test_domain_id')

    def test_list_projects(self):
        projects = [
            openstack.identity.v3.project.Project(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_project_1',
                'description': 'Testing Project 1',
                'domain_id': 'test_domain_id',
                'enabled': True,
                'is_domain': True,
                'links': ['test1', 'test2'],
                'parent_id': 'test_parent_id'
            }),
            openstack.identity.v3.project.Project(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': 'test_project_1',
                'description': 'Testing Project 1',
                'domain_id': 'test_domain_id',
                'enabled': True,
                'is_domain': True,
                'links': ['test1', 'test2'],
                'parent_id': 'test_parent_id'
            }),
        ]

        self.fake_client.projects = mock.MagicMock(return_value=projects)
        response = self.project_instance.list()
        self.assertEqual(len(response), 2)

    def test_create_project(self):
        project = {
            'name': 'test_project',
            'description': 'Testing Project',
            'domain_id': 'test_domain_id',
            'enabled': True,
            'is_domain': True,
            'tags': ['test1', 'test2'],
            'parent_id': 'test_parent_id'
        }

        new_res = openstack.identity.v3.project.Project(**project)
        self.project_instance.config = project
        self.fake_client.create_project = mock.MagicMock(return_value=new_res)

        response = self.project_instance.create()
        self.assertEqual(response.name, project['name'])
        self.assertEqual(response.description, project['description'])

    def test_update_project(self):
        old_project = openstack.identity.v3.project.Project(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_project',
            'description': 'Testing Project',
            'domain_id': 'test_domain_id',
            'enabled': True,
            'is_domain': True,
            'links': ['test1', 'test2'],
            'parent_id': 'test_parent_id'

        })

        new_config = {
            'name': 'test_project_updated',
            'domain_id': 'test_updated_domain_id',
            'description': 'Testing Project 1',
            'enabled': False,
            'is_domain': False,
        }

        new_project = openstack.identity.v3.project.Project(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_project_updated',
            'description': 'Testing Project 1',
            'domain_id': 'test_updated_domain_id',
            'enabled': False,
            'is_domain': False,
            'links': ['test1', 'test2'],
            'parent_id': 'test_parent_id'

        })

        self.project_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_project = mock.MagicMock(return_value=old_project)
        self.fake_client.update_project =\
            mock.MagicMock(return_value=new_project)

        response = self.project_instance.update(new_config=new_config)
        self.assertNotEqual(response.name, old_project.name)
        self.assertNotEqual(response.is_enabled, old_project.is_enabled)
        self.assertNotEqual(response.description, old_project.description)
        self.assertNotEqual(response.is_domain, old_project.is_domain)

    def test_delete_project(self):
        project = openstack.identity.v3.project.Project(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_project',
            'description': 'Testing Project',
            'domain_id': 'test_domain_id',
            'enabled': True,
            'is_domain': True,
            'links': ['test1', 'test2'],
            'parent_id': 'test_parent_id'
        })

        self.project_instance.resource_id = \
            'a95b5509-c122-4c2f-823e-884bb559afe8'
        self.fake_client.get_project = mock.MagicMock(return_value=project)
        self.fake_client.delete_project = mock.MagicMock(return_value=None)

        response = self.project_instance.delete()
        self.assertIsNone(response)
