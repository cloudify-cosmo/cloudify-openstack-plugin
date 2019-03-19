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

# Standard Imports
from os import getenv
import time
import StringIO
import unittest

# Third party imports
import openstack
import requests
import requests.exceptions
from fabric.api import settings as fabric_settings, run as fabric_run
from cloudify.workflows import local

# Local imports
import resource_interface_mappings


IGNORED_LOCAL_WORKFLOW_MODULES = (
    'worker_installer.tasks',
    'plugin_installer.tasks',
    'cloudify_agent.operations',
    'cloudify_agent.installer.operations',
)

RETRY_MAX = 10
RETRY_INT = 1


class TestEnvironmentValidationError(Exception):
    pass


class LiveUseCaseTests(unittest.TestCase):
    """ Test a use case using a "local" Cloudify Workflow.

    Write a blueprint for a particular use case,
    for example creating a port with allowed address pairs.

    You need the client config in your inputs, e.g.:
    ```yaml
      auth_url:
        type: string

      username:
        type: string

      password:
        type: string

      region_name:
        type: string

      project_name:
        type: string
    ```

    To setup your test environment in PyCharm,
    add the following environment variables:

    ```bash
    openstack_username=.......;openstack_password=.........;
    openstack_project_name=.....;openstack_region_name=RegionOne;
    openstack_auth_url=https://....;=
    ```

    """

    def setUp(self):
        super(LiveUseCaseTests, self).setUp()

    @property
    def client_config(self):
        return {
            'auth_url': getenv('openstack_auth_url'),
            'username': getenv('openstack_username'),
            'password': getenv('openstack_password'),
            'project_name': getenv('openstack_project_name'),
            'region_name': getenv('openstack_region_name'),
        }

    @staticmethod
    def resolve_resource_interface(node_type):
        try:
            return getattr(
                resource_interface_mappings, node_type.split('.')[-1])
        except AttributeError:
            return None

    def get_resource_interfaces(self):
        resource_interface_list = []
        for node_instance in self.cfy_local.storage.get_node_instances():
            node_template = \
                self.cfy_local.storage.get_node(node_instance.node_id)
            resource_interface = \
                self.resolve_resource_interface(
                    node_template.type)
            if not resource_interface:
                continue
            if node_template.properties['use_external_resource']:
                continue
            resource_identifier = \
                node_template.properties['resource_config'].get('name') or \
                node_template.properties['resource_config'].get('id')
            if not resource_identifier:
                raise Exception('Test blueprints must provide name or id.')
            resource_interface_list.append(
                resource_interface(resource_identifier, self.client_config))
        return resource_interface_list

    def verify_no_conflicting_resources(self):
        """ This method checks that there are no conflicting resources in
        Openstack before we run a test.
        :return: Nothing.
        :Raises Exception: Raises an exception if there are such resources.
        """
        for resource_interface in self.get_resource_interfaces():
            try:
                conflicting_resource = resource_interface.get()
            except openstack.exceptions.HttpException:
                continue
            raise TestEnvironmentValidationError(
                'Conflicting resource found {0}'.format(conflicting_resource))

    def delete_all_resources(self):
        """Deletes orphan resources in Openstack.
        :return: Nothing.
        """
        for resource_interface in self.get_resource_interfaces():
            try:
                resource_interface.delete()
            except openstack.exceptions.SDKException:
                pass

    def initialize_local_blueprint(self):
        self.cfy_local = local.init_env(
            self.blueprint_path,
            self.test_name,
            inputs=self.inputs,
            ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES)
        self.verify_no_conflicting_resources()

    def install_blueprint(self,
                          task_retries=RETRY_MAX,
                          task_retry_interval=RETRY_INT):

        self.cfy_local.execute(
            'install',
            task_retries=task_retries,
            task_retry_interval=task_retry_interval)

    def uninstall_blueprint(self,
                            task_retries=RETRY_MAX,
                            task_retry_interval=RETRY_INT,
                            ignore_failure=False):

        if ignore_failure:
            self.cfy_local.execute(
                'uninstall',
                parameters={'ignore_failure': True},
                task_retries=task_retries,
                task_retry_interval=task_retry_interval)
        else:
            self.cfy_local.execute(
                'uninstall',
                task_retries=task_retries,
                task_retry_interval=task_retry_interval)

    def cleanup_uninstall(self):
        self.uninstall_blueprint(ignore_failure=True)

    def test_keypair_example(self, *_):
        self.test_name = 'test_keypair_example'
        self.blueprint_path = './examples/local/keypair.yaml'
        self.inputs = dict(self.client_config)
        self.initialize_local_blueprint()
        self.install_blueprint()
        self.uninstall_blueprint()

    def test_server_group_example(self, *_):
        self.test_name = 'test_server_group_example'
        self.blueprint_path = './examples/local/server_group.yaml'
        self.inputs = dict(self.client_config)
        self.initialize_local_blueprint()
        self.install_blueprint()
        self.uninstall_blueprint()

    # Requires Special Permissions
    def test_volume_type_example(self, *_):
        self.test_name = 'test_volume_type_example'
        self.blueprint_path = './examples/local/volume_type.yaml'
        self.inputs = dict(self.client_config)
        self.initialize_local_blueprint()
        # execute install workflow
        self.cfy_local.execute(
            'install',
            task_retries=30,
            task_retry_interval=1)
        # execute uninstall workflow
        self.cfy_local.execute(
            'uninstall',
            task_retries=30,
            task_retry_interval=1)

    def test_network_example(self, *_):
        self.test_name = 'test_network_example'
        self.blueprint_path = './examples/local/network.yaml'
        self.inputs = dict(self.client_config)
        self.inputs.update(
            {
                'example_subnet_cidr': '10.10.0.0/24',
                'example_fixed_ip': '10.10.0.11',
                'name_prefix': 'network_'
            }
        )
        self.initialize_local_blueprint()
        self.install_blueprint()
        self.uninstall_blueprint()

    def test_blueprint_example(self, *_):
        self.test_name = 'test_blueprint_example'
        self.blueprint_path = './examples/local/blueprint.yaml'
        self.inputs = dict(self.client_config)
        self.inputs.update(
            {
                'external_network_id': 'dda079ce-12cf-4309-879a-8e67aec94de4',
                'example_subnet_cidr': '10.10.0.0/24',
                'name_prefix': 'blueprint_',
                'image_id': 'e41430f7-9131-495b-927f-e7dc4b8994c8',
                'flavor_id': '3',
                'agent_user': 'ubuntu'
            }
        )
        self.initialize_local_blueprint()
        self.install_blueprint()
        time.sleep(10)
        private_key = StringIO.StringIO()
        try:
            server_floating_ip = \
                self.cfy_local.storage.get_node_instances(
                    'example-floating_ip_address')[0]
            server_key_instance = \
                self.cfy_local.storage.get_node_instances(
                    'example-keypair')[0]
            ip_address = \
                server_floating_ip.runtime_properties[
                    'floating_ip_address']
            private_key.write(
                server_key_instance.runtime_properties['private_key'])
            private_key.pos = 0
        except (KeyError, IndexError) as e:
            raise Exception('Missing Runtime Property: {0}'.format(str(e)))

        with fabric_settings(
                host_string=ip_address,
                key=private_key.read(),
                user=self.inputs.get('agent_user'),
                abort_on_prompts=True):
            fabric_run_output = fabric_run('last')
            self.assertEqual(0, fabric_run_output.return_code)

        # execute uninstall workflow
        self.uninstall_blueprint()

    def test_hello_world_example(self, *_):
        self.addCleanup(self.cleanup_uninstall)
        self.test_name = 'test_hello_world_example'
        self.blueprint_path = \
            './examples/cloudify-hello-world-example/openstack.yaml'
        self.inputs = dict(self.client_config)
        self.inputs.update(
            {
                'external_network_id': 'dda079ce-12cf-4309-879a-8e67aec94de4',
                'name_prefix': 'hello_world',
                'image': 'e41430f7-9131-495b-927f-e7dc4b8994c8',
                'flavor': '2',
            }
        )
        self.initialize_local_blueprint()
        self.install_blueprint()
        time.sleep(10)

        try:
            server_floating_ip = \
                self.cfy_local.storage.get_node_instances('ip')[0]
            ip_address = \
                server_floating_ip.runtime_properties[
                    'floating_ip_address']

            # Before checking the response returned from the apache server
            # installed on the server of this blueprint, it could take up to
            # 30 seconds or less to be up and running, so that we need to
            # have to wait this time
            timeout = 30
            current_time = time.time()
            is_up = False

            while not is_up and time.time() <= timeout + current_time:
                try:
                    response = requests.get('http://{0}'.format(ip_address))
                    self.assertEqual(response.status_code, 200)
                    is_up = True
                except requests.exceptions.ConnectionError:
                    pass

            if not is_up:
                raise Exception(
                    'Server is not responding,'
                    ' please check your blueprint configuration')

        except (KeyError, IndexError) as e:
            raise Exception('Missing Runtime Property: {0}'.format(str(e)))
        # execute uninstall workflow
        self.uninstall_blueprint()
