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

DEVELOPMENT_ROOT = os.environ.get(
    'REPO_BASE',
    os.path.join(os.path.expanduser('~'), 'dev/repos'))
PLUGIN_NAME = 'cloudify-openstack-plugin'


class OpenstackPluginTestCase(PluginsTest):

    base_path = os.path.dirname(os.path.realpath(__file__))

    @property
    def plugin_root_directory(self):
        return os.path.join(DEVELOPMENT_ROOT, PLUGIN_NAME)

    @property
    def inputs(self):
        return {
            'region': os.getenv('openstack_region_name',
                                'RegionOne'),
            'external_network_id': os.getenv(
                'external_network_id',
                'dda079ce-12cf-4309-879a-8e67aec94de4'),
            'image': 'e41430f7-9131-495b-927f-e7dc4b8994c8',
            'flavor': '3',
        }

    def create_secrets(self):
        secrets = {
            'agent_key_private': os.getenv('agent_key_private',
                                           open('/tmp/foo.rsa').read()),
            'agent_key_public': os.getenv('agent_key_public',
                                          open('/tmp/foo.rsa.pub').read()),
            'openstack_auth_url': os.getenv('openstack_auth_url'),
            'openstack_username': os.getenv('openstack_username'),
            'openstack_password': os.getenv('openstack_password'),
            'openstack_project_name': os.getenv('openstack_project_name',
                                                os.getenv(
                                                    'openstack_tenant_name')),
            'openstack_tenant_name': os.getenv('openstack_tenant_name'),
            'openstack_region': os.getenv('openstack_region_name',
                                          'RegionOne'),
            'base_image_id': '70de1e0f-2951-4eae-9a8f-05afd97cd036',
            'base_flavor_id': '3',
        }
        self._create_secrets(secrets)

    def upload_plugins(self):
        self.upload_mock_plugin(
            PLUGIN_NAME,
            os.path.join(DEVELOPMENT_ROOT, PLUGIN_NAME))
        self.upload_mock_plugin(
            'cloudify-utilities-plugin',
            os.path.join(DEVELOPMENT_ROOT, 'cloudify-utilities-plugin'))
        self.upload_mock_plugin(
            'cloudify-ansible-plugin',
            os.path.join(DEVELOPMENT_ROOT, 'cloudify-ansible-plugin'))

    def test_blueprints(self):
        self.upload_plugins()
        self.create_secrets()
        self.check_hello_world_blueprint('openstack', self.inputs, 400)
        self.check_db_lb_app_blueprint(
            'openstack',
            1800,
            network_inputs={
                'external_network_id': os.getenv(
                    'external_network_id',
                    'dda079ce-12cf-4309-879a-8e67aec94de4'),
            }
        )
