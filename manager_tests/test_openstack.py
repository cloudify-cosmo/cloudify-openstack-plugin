# Built-in Imports
import os
from time import sleep

# Cloudify Imports
from ecosystem_tests import TestLocal, utils, labs


class TestOpenstack(TestLocal):

    def inputs(self):
        pass

    def setup_cfy_local(self):
        pass

    def add_os_environment_variables(self):

        secrets = {
            'keystone_username': 'OS_USERNAME',
            'keystone_password': 'OS_PASSWORD',
            'keystone_tenant_name': 'OS_TENANT_NAME',
            'keystone_region': 'OS_REGION_NAME',
            'keystone_url': 'OS_AUTH_URL'
        }

        for secret_key, env_key in secrets.items():
            env_value = utils.get_secrets(secret_key)
            os.environ[env_key] = env_value.value

    def check_openstack_resource(
            self, resource_id, resource_type, exists=True, command=None):

        if command:
            pass
        elif 'Router' in resource_type:
            command = 'neutron router-show {0}'.format(resource_id)
        elif 'Subnet' in resource_type:
            command = 'neutron subnet-show {0}'.format(resource_id)
        elif 'Network' in resource_type:
            command = 'neutron net-show {0}'.format(resource_id)
        elif 'Port' in resource_type:
            command = 'neutron port-show {0}'.format(resource_id)
        elif 'SecurityGroup' in resource_type:
            command = 'neutron security-group-show {0}'.format(resource_id)
        elif 'FloatingIP' in resource_type:
            command = 'neutron floatingip-show {0}'.format(resource_id)
        elif 'cloudify.openstack.nodes.Server' in resource_type:
            command = 'nova show {0}'.format(resource_id)
        elif 'ServerGroup' in resource_type:
            command = 'nova server-group-get {0}'.format(resource_id)
        else:
            raise Exception('Unsupported type {0} for {1}.'.format(
                resource_type, resource_id))
        self.assertEqual(0 if exists else 1, utils.execute_command(command))

    def check_resources_in_deployment_created(self, nodes, node_names):
        for node in nodes:
            print 'Checking resource created: {0}'.format(node)
            if node['id'] not in node_names:
                break
            external_id = \
                node['instances'][0]['runtime_properties'].get('external_id')
            self.check_openstack_resource(external_id, node['node_type'])

    def check_resources_in_deployment_deleted(self, nodes, node_names):
        for node in nodes:
            if node['id'] not in node_names:
                break
            self.check_openstack_resource(
                node['instances'][0]['runtime_properties']['external_id'],
                node['node_type'], exists=False)

    def install_manager(self):
        self.manager_ip = labs.create_lab()

    def uninstall_manager(self):
        labs.delete_lab()

    def upload_plugins(self):

        sleep(5)
        utils.update_plugin_yaml(
            os.environ['CIRCLE_SHA1'], 'openstack')
        workspace_path = os.path.join(
            os.path.abspath('workspace'),
            'build')
        sleep(5)
        utils.upload_plugin(utils.get_wagon_path(workspace_path))
        sleep(5)
        for plugin in self.plugins_to_upload:
            utils.upload_plugin(plugin[0], plugin[1])

    def setUp(self):

        sensitive_data = [
            os.environ['LAB_PASSWORD'],
            os.environ['LAB_SERVER'],
            os.environ['LAB_USERNAME']
        ]
        super(TestOpenstack, self).setUp(
            'openstack.yaml', sensitive_data=sensitive_data)

        os.environ['TEST_APPLICATION_PREFIX'] = \
            os.environ['CIRCLE_BUILD_NUM']

        if 'ECOSYSTEM_SESSION_MANAGER_IP' not in os.environ:
            self.install_manager()
            self.addCleanup(self.uninstall_manager)
            self.password = 'admin'
        os.environ['ECOSYSTEM_SESSION_PASSWORD'] = self.password
        os.environ['ECOSYSTEM_SESSION_MANAGER_IP'] = self.manager_ip
        sleep(300)
        utils.initialize_cfy_profile(
            '{0} -u admin -p {1} -t default_tenant'.format(
                self.manager_ip, self.password))
        self.upload_plugins()
        self.add_os_environment_variables()

    def cleanup_network_deployment(self):
        # This is just for cleanup.
        # Because its in the lab, don't care if it passes or fails.
        utils.execute_command(
            'cfy uninstall -p ignore_failure=true openstack-example-network')

    def port_fixed_ip_deployment(self):
        openstack_nodes = [
            'port'
        ]
        utils.execute_command(
            'cfy blueprints upload blueprints/port-fixed-ip.yaml '
            '-b fixed-ip')
        # Create Deployment (Blueprint already uploaded.)
        if utils.create_deployment(
                'fixed-ip', inputs={'fixed_ip': '192.168.113.250'}):
            raise Exception(
                'Deployment fixed-ip failed.')
        # Install Deployment.
        if utils.execute_install('fixed-ip'):
            raise Exception(
                'Install fixed-ip failed.')
        # Get list of nodes in the deployment.
        deployment_nodes = \
            utils.get_deployment_resources_by_node_type_substring(
                'fixed-ip', 'cloudify.openstack.nodes.Port')
        # Check that we assigned the desired fixed IP.
        fixed_ip_node = \
            [node for node in deployment_nodes if node['id'] == 'port']
        fixed_ip_instance = \
            fixed_ip_node[0]['instances'][0]['runtime_properties']
        if '192.168.113.250' != fixed_ip_instance['fixed_ip_address']:
            raise Exception('IP Not Set.')
        # Check that the nodes really exist.
        self.check_resources_in_deployment_created(
            deployment_nodes, openstack_nodes)
        # Uninstall this deployment.
        if utils.execute_uninstall('fixed-ip'):
            raise Exception('Uninstall fixed-ip failed.')
        # Check that the nodes no longer exist.
        self.check_resources_in_deployment_deleted(
            deployment_nodes,
            openstack_nodes)

    def nodecellar_deployment(self):
        # Create a set of nodes to check.
        openstack_nodes = [
            'nodecellar_ip',
            'haproxy_frontend_security_group',
            'nodecellar_security_group',
            'haproxy_host_port',
            'nodejs_host_port',
            'mongodb_host_port'
        ]
        # Create another set of nodes to check.
        monitored_nodes = [
            'haproxy_frontend_host',
            'nodejs_host',
            'mongod_host'
        ]
        # Install the deployment
        if utils.install_nodecellar(
                blueprint_file_name=self.blueprint_file_name):
            raise Exception('Nodecellar install failed.')
        # Scale the deployment.
        if utils.execute_scale(
                'nc', scalable_entity_name='nodejs_host_scale_group'):
            raise Exception('Nodecellar scale failed.')
        # Get list of nodes in the deployment.
        deployment_nodes = \
            utils.get_deployment_resources_by_node_type_substring(
                'nc', 'cloudify')
        # Check that the nodes were created.
        self.check_resources_in_deployment_created(
            deployment_nodes, openstack_nodes)
        self.check_resources_in_deployment_created(
            deployment_nodes, monitored_nodes)
        # Uninstall the deployment.
        if utils.execute_uninstall('nc'):
            raise Exception('Nodecellar uninstall failed.')
        # Check that the nodes were deleted.
        self.check_resources_in_deployment_deleted(
            deployment_nodes,
            openstack_nodes)
        self.check_resources_in_deployment_deleted(
            deployment_nodes,
            monitored_nodes)

    def network_deployment(self):
        # Create a list of node templates to verify.
        openstack_nodes = [
            'private_subnet',
            'public_subnet',
            'public_network_router',
            'private_network',
            'public_network',
            'external_network'
        ]
        # Add delete deployment to cleanup even though we can trash the lab.
        # Deployment already exists. But installed with wrong plugin.
        utils.execute_command(
            'cfy executions start uninstall -d openstack-example-network')
        utils.execute_command(
            'cfy deployments delete openstack-example-network')
        self.addCleanup(self.cleanup_network_deployment)
        # Create Deployment (Blueprint already uploaded.)
        if utils.create_deployment(
                'openstack-example-network',
                inputs={'external_network_name': 'external_network'}):
            raise Exception(
                'Deployment openstack-example-network failed.')
        # Install Deployment.
        if utils.execute_install('openstack-example-network'):
            raise Exception(
                'Install openstack-example-network failed.')
        # Get list of nodes in the deployment.
        deployment_nodes = \
            utils.get_deployment_resources_by_node_type_substring(
                'nc', 'cloudify.openstack.nodes')
        # Check that the nodes really exist.
        self.check_resources_in_deployment_created(
            deployment_nodes, openstack_nodes)
        # Test another deployments that requires this deployment.
        self.nodecellar_deployment()
        self.port_fixed_ip_deployment()
        # Uninstall this deployment.
        if utils.execute_uninstall('openstack-example-network'):
            raise Exception('Uninstall openstack-example-network failed.')
        # Check that the nodes no longer exist.
        self.check_resources_in_deployment_deleted(
            deployment_nodes,
            openstack_nodes)

    def server_groups_deployment(self):
        # Create a list of node templates to verify.
        openstack_nodes = [
            'router',
            'public_network',
            'public_subnet',
            'public_ip',
            'server_groups_example_security_group',
            'public_subnet_nic',
            'example_key',
            'server_group',
            'server_group_member',
        ]
        utils.execute_command(
            'cfy blueprints upload blueprints/server-groups.yaml '
            '-b server-groups')
        # Create Deployment (Blueprint already uploaded.)
        if utils.create_deployment('server-groups'):
            raise Exception(
                'Deployment server-groups failed.')
        # Install Deployment.
        if utils.execute_install('server-groups'):
            raise Exception(
                'Install server-groups failed.')
        # Get list of nodes in the deployment.
        deployment_nodes = \
            utils.get_deployment_resources_by_node_type_substring(
                'server-groups', 'cloudify.openstack.nodes')
        # Check that the nodes really exist.
        self.check_resources_in_deployment_created(
            deployment_nodes, openstack_nodes)
        # Uninstall this deployment.
        if utils.execute_uninstall('server-groups'):
            raise Exception('Uninstall server-groups failed.')
        # Check that the nodes no longer exist.
        self.check_resources_in_deployment_deleted(
            deployment_nodes,
            openstack_nodes)

    def deployments(self):
        self.network_deployment()
        self.server_groups_deployment()

    def test_run_tests(self):
        self.deployments()
