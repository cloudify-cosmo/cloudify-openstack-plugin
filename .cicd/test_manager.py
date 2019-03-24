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

import os

from integration_tests.tests.test_cases import PluginsTest
from integration_tests.tests import utils as test_utils

PLUGIN_NAME = 'cloudify-openstacksdk-plugin'


class OpenstackPluginTestCase(PluginsTest):

    base_path = os.path.dirname(os.path.realpath(__file__))

    @property
    def plugin_root_directory(self):
        return os.path.abspath(os.path.join(self.base_path, '..'))

    @property
    def client_config(self):
        return {
            'auth_url': os.getenv('openstack_auth_url'),
            'username': os.getenv('openstack_username'),
            'password': os.getenv('openstack_password'),
            'project_name': os.getenv('openstack_project_name'),
            'region_name': os.getenv('openstack_region_name'),
        }

    def check_main_blueprint(self):
        blueprint_id = 'manager_blueprint'
        self.inputs = dict(self.client_config)
        self.inputs.update(
            {
                'external_network_id': os.getenv(
                    'external_network_id',
                    'dda079ce-12cf-4309-879a-8e67aec94de4'),
                'example_subnet_cidr': '10.10.0.0/24',
                'name_prefix': 'blueprint_',
                'image_id': 'e41430f7-9131-495b-927f-e7dc4b8994c8',
                'flavor_id': '3',
                'agent_user': 'ubuntu'
            }
        )
        dep, ex_id = self.deploy_application(
            test_utils.get_resource(
                os.path.join(
                    self.plugin_root_directory,
                    'examples/manager/blueprint.yaml')),
            timeout_seconds=200,
            blueprint_id=blueprint_id,
            deployment_id=blueprint_id,
            inputs=self.inputs)
        self.undeploy_application(dep.id)

    def test_blueprints(self):
        self.upload_mock_plugin(PLUGIN_NAME, self.plugin_root_directory)
        self.check_main_blueprint()
