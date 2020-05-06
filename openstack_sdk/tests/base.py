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


# Third party imports
from openstack import exceptions


class OpenStackSDKTestBase(unittest.TestCase):

    def setUp(self):
        super(OpenStackSDKTestBase, self).setUp()
        self.connection = mock.patch('openstack.connect', mock.MagicMock())

    def tearDown(self):
        super(OpenStackSDKTestBase, self).tearDown()

    def get_openstack_connections(self):
        return {
            'server': self._fake_compute_server,
            'server_group': self._fake_compute_server_group,
            'host_aggregate': self._fake_compute_host_aggregate,
            'key_pair': self._fake_compute_key_pair,
            'image': self._fake_image,
            'flavor': self._fake_compute_flavor,
            'port': self._fake_network_port,
            'network': self._fake_network,
            'subnet': self._fake_network_subnet,
            'floating_ip': self._fake_network_floating_ip,
            'router': self._fake_network_router,
            'security_group': self._fake_network_security_group,
            'security_group_rule': self._fake_network_security_group_rule,
            'volume': self._fake_block_storage_volume,
            'volume_attachment': self._fake_compute_volume_attachment,
            'volume_type': self._fake_block_storage_type,
            'backup': self._fake_block_storage_backup,
            'snapshot': self._fake_block_storage_snapshot,
            'user': self._fake_identity_user,
            'group': self._fake_identity_group,
            'role': self._fake_identity_role,
            'project': self._fake_identity_project,
            'rbac_policy': self._fake_network_rbac_policy,
            'dns': self._fake_dns,
        }

    @property
    def client_config(self):
        return {
            'auth_url': 'test_auth_url',
            'username': 'test_username',
            'password': 'test_password',
            'project_name': 'test_project_name',
            'region_name': 'test_region_name'
        }

    def _gen_openstack_sdk_error(self, message='SomeThingIsGoingWrong'):
        return mock.MagicMock(
            side_effect=exceptions.SDKException(message=message))

    def generate_fake_openstack_connection(self, service_type):
        return self.get_openstack_connections()[service_type]()

    def _fake_compute_server(self):
        server_conn = mock.MagicMock()
        server_conn.servers = self._gen_openstack_sdk_error()
        server_conn.get_server = self._gen_openstack_sdk_error()
        server_conn.create_server = self._gen_openstack_sdk_error()
        server_conn.delete_server = self._gen_openstack_sdk_error()
        server_conn.reboot_server = self._gen_openstack_sdk_error()
        server_conn.resume_server = self._gen_openstack_sdk_error()
        server_conn.suspend_server = self._gen_openstack_sdk_error()
        server_conn.backup_server = self._gen_openstack_sdk_error()
        server_conn.rebuild_server = self._gen_openstack_sdk_error()
        server_conn.create_server_image = self._gen_openstack_sdk_error()
        server_conn.update_server = self._gen_openstack_sdk_error()
        server_conn.start_server = self._gen_openstack_sdk_error()
        server_conn.stop_server = self._gen_openstack_sdk_error()
        server_conn.get_server_password = self._gen_openstack_sdk_error()
        server_conn.volume_attachments = self._gen_openstack_sdk_error()
        server_conn.get_volume_attachment = self._gen_openstack_sdk_error()
        server_conn.create_volume_attachment = self._gen_openstack_sdk_error()
        server_conn.delete_volume_attachment = self._gen_openstack_sdk_error()
        server_conn.create_server_interface = self._gen_openstack_sdk_error()
        server_conn.delete_server_interface = self._gen_openstack_sdk_error()
        server_conn.get_server_interface = self._gen_openstack_sdk_error()
        server_conn.server_interfaces = self._gen_openstack_sdk_error()
        server_conn.add_security_group_to_server = \
            self._gen_openstack_sdk_error()
        server_conn.remove_security_group_from_server = \
            self._gen_openstack_sdk_error()
        server_conn.add_floating_ip_to_server = \
            self._gen_openstack_sdk_error()
        server_conn.remove_floating_ip_from_server = \
            self._gen_openstack_sdk_error()

        self.connection.compute = server_conn
        return self.connection.compute

    def _fake_compute_host_aggregate(self):
        host_aggregate_conn = mock.MagicMock()
        host_aggregate_conn.aggregates = self._gen_openstack_sdk_error()
        host_aggregate_conn.get_aggregate = self._gen_openstack_sdk_error()
        host_aggregate_conn.create_aggregate = self._gen_openstack_sdk_error()
        host_aggregate_conn.delete_aggregate = self._gen_openstack_sdk_error()
        host_aggregate_conn.update_aggregate = self._gen_openstack_sdk_error()

        self.connection.compute = host_aggregate_conn
        return self.connection.compute

    def _fake_compute_server_group(self):
        server_group_conn = mock.MagicMock()
        server_group_conn.server_groups = self._gen_openstack_sdk_error()
        server_group_conn.get_server_group = self._gen_openstack_sdk_error()
        server_group_conn.create_server_group = self._gen_openstack_sdk_error()
        server_group_conn.delete_server_group = self._gen_openstack_sdk_error()

        self.connection.compute = server_group_conn
        return self.connection.compute

    def _fake_compute_key_pair(self):
        key_pair_conn = mock.MagicMock()
        key_pair_conn.keypairs = self._gen_openstack_sdk_error()
        key_pair_conn.get_keypair = self._gen_openstack_sdk_error()
        key_pair_conn.create_keypair = self._gen_openstack_sdk_error()
        key_pair_conn.delete_keypair = self._gen_openstack_sdk_error()
        key_pair_conn.update_keypair = self._gen_openstack_sdk_error()

        self.connection.compute = key_pair_conn
        return self.connection.compute

    def _fake_compute_flavor(self):
        flavor_conn = mock.MagicMock()
        flavor_conn.flavors = self._gen_openstack_sdk_error()
        flavor_conn.get_flavor = self._gen_openstack_sdk_error()
        flavor_conn.create_flavor = self._gen_openstack_sdk_error()
        flavor_conn.delete_flavor = self._gen_openstack_sdk_error()

        self.connection.compute = flavor_conn
        return self.connection.compute

    def _fake_compute_volume_attachment(self):
        volume_attachment = mock.MagicMock()
        volume_attachment.volume_attachments = self._gen_openstack_sdk_error()

        volume_attachment.get_volume_attachment =\
            self._gen_openstack_sdk_error()

        volume_attachment.create_volume_attachment =\
            self._gen_openstack_sdk_error()

        volume_attachment.delete_volume_attachment =\
            self._gen_openstack_sdk_error()

        volume_attachment.update_volume_attachment =\
            self._gen_openstack_sdk_error()

        self.connection.compute = volume_attachment
        return self.connection.compute

    def _fake_image(self):
        image_conn = mock.MagicMock()
        image_conn.images = self._gen_openstack_sdk_error()
        image_conn.get_image = self._gen_openstack_sdk_error()
        image_conn.upload_image = self._gen_openstack_sdk_error()
        image_conn.delete_image = self._gen_openstack_sdk_error()
        image_conn.update_image = self._gen_openstack_sdk_error()

        self.connection.image = image_conn
        return self.connection.image

    def _fake_network(self):
        network_conn = mock.MagicMock()
        network_conn.networks = self._gen_openstack_sdk_error()
        network_conn.get_network = self._gen_openstack_sdk_error()
        network_conn.create_network = self._gen_openstack_sdk_error()
        network_conn.delete_network = self._gen_openstack_sdk_error()
        network_conn.update_network = self._gen_openstack_sdk_error()

        self.connection.network = network_conn
        return self.connection.network

    def _fake_network_subnet(self):
        subnet_conn = mock.MagicMock()
        subnet_conn.subnets = self._gen_openstack_sdk_error()
        subnet_conn.get_subnet = self._gen_openstack_sdk_error()
        subnet_conn.create_subnet = self._gen_openstack_sdk_error()
        subnet_conn.delete_subnet = self._gen_openstack_sdk_error()
        subnet_conn.update_subnet = self._gen_openstack_sdk_error()

        self.connection.network = subnet_conn
        return self.connection.network

    def _fake_network_port(self):
        port_conn = mock.MagicMock()
        port_conn.ports = self._gen_openstack_sdk_error()
        port_conn.get_port = self._gen_openstack_sdk_error()
        port_conn.create_port = self._gen_openstack_sdk_error()
        port_conn.delete_port = self._gen_openstack_sdk_error()
        port_conn.update_port = self._gen_openstack_sdk_error()

        self.connection.network = port_conn
        return self.connection.network

    def _fake_network_router(self):
        router_conn = mock.MagicMock()
        router_conn.routers = self._gen_openstack_sdk_error()
        router_conn.get_router = self._gen_openstack_sdk_error()
        router_conn.create_router = self._gen_openstack_sdk_error()
        router_conn.delete_router = self._gen_openstack_sdk_error()
        router_conn.update_router = self._gen_openstack_sdk_error()

        self.connection.network = router_conn
        return self.connection.network

    def _fake_network_floating_ip(self):
        floating_ip_conn = mock.MagicMock()
        floating_ip_conn.ips = self._gen_openstack_sdk_error()
        floating_ip_conn.get_ip = self._gen_openstack_sdk_error()
        floating_ip_conn.create_ip = self._gen_openstack_sdk_error()
        floating_ip_conn.delete_ip = self._gen_openstack_sdk_error()
        floating_ip_conn.update_ip = self._gen_openstack_sdk_error()

        self.connection.network = floating_ip_conn
        return self.connection.network

    def _fake_network_security_group(self):
        security_group_conn = mock.MagicMock()

        security_group_conn.security_groups = self._gen_openstack_sdk_error()

        security_group_conn.get_security_group =\
            self._gen_openstack_sdk_error()

        security_group_conn.create_security_group =\
            self._gen_openstack_sdk_error()

        security_group_conn.delete_security_group =\
            self._gen_openstack_sdk_error()

        security_group_conn.update_security_group =\
            self._gen_openstack_sdk_error()

        self.connection.network = security_group_conn
        return self.connection.network

    def _fake_network_security_group_rule(self):
        security_group_rule_conn = mock.MagicMock()

        security_group_rule_conn.security_group_rules =\
            self._gen_openstack_sdk_error()

        security_group_rule_conn.get_security_group_rule = \
            self._gen_openstack_sdk_error()

        security_group_rule_conn.create_security_group_rule = \
            self._gen_openstack_sdk_error()

        security_group_rule_conn.delete_security_group_rule = \
            self._gen_openstack_sdk_error()

        self.connection.network = security_group_rule_conn
        return self.connection.network

    def _fake_network_rbac_policy(self):
        rbac_policy_conn = mock.MagicMock()
        rbac_policy_conn.rbac_policies = self._gen_openstack_sdk_error()
        rbac_policy_conn.get_rbac_policy = self._gen_openstack_sdk_error()
        rbac_policy_conn.create_rbac_policy = self._gen_openstack_sdk_error()
        rbac_policy_conn.delete_rbac_policy = self._gen_openstack_sdk_error()
        rbac_policy_conn.update_rbac_policy = self._gen_openstack_sdk_error()
        self.connection.network = rbac_policy_conn
        return self.connection.network

    def _fake_block_storage_volume(self):
        volume_conn = mock.MagicMock()
        volume_conn.volumes = self._gen_openstack_sdk_error()
        volume_conn.get_volume = self._gen_openstack_sdk_error()
        volume_conn.create_volume = self._gen_openstack_sdk_error()
        volume_conn.delete_volume = self._gen_openstack_sdk_error()
        volume_conn.extend_volume = self._gen_openstack_sdk_error()
        self.connection.block_storage = volume_conn
        return self.connection.block_storage

    def _fake_block_storage_type(self):
        type_vol = mock.MagicMock()
        type_vol.types = self._gen_openstack_sdk_error()
        type_vol.get_type = self._gen_openstack_sdk_error()
        type_vol.create_type = self._gen_openstack_sdk_error()
        type_vol.delete_type = self._gen_openstack_sdk_error()
        self.connection.block_storage = type_vol
        return self.connection.block_storage

    def _fake_block_storage_snapshot(self):
        snapshot = mock.MagicMock()
        snapshot.snapshots = self._gen_openstack_sdk_error()
        snapshot.get_snapshot = self._gen_openstack_sdk_error()
        snapshot.create_snapshot = self._gen_openstack_sdk_error()
        snapshot.delete_snapshot = self._gen_openstack_sdk_error()
        self.connection.block_storage = snapshot
        return self.connection.block_storage

    def _fake_block_storage_backup(self):
        backup = mock.MagicMock()
        backup.backups = self._gen_openstack_sdk_error()
        backup.get_backup = self._gen_openstack_sdk_error()
        backup.create_backup = self._gen_openstack_sdk_error()
        backup.delete_backup = self._gen_openstack_sdk_error()
        backup.restore_backup = self._gen_openstack_sdk_error()
        self.connection.block_storage = backup
        return self.connection.block_storage

    def _fake_identity_user(self):
        user_conn = mock.MagicMock()
        user_conn.users = self._gen_openstack_sdk_error()
        user_conn.get_user = self._gen_openstack_sdk_error()
        user_conn.create_user = self._gen_openstack_sdk_error()
        user_conn.delete_user = self._gen_openstack_sdk_error()
        user_conn.update_user = self._gen_openstack_sdk_error()
        self.connection.identity = user_conn
        return self.connection.identity

    def _fake_identity_group(self):
        group_conn = mock.MagicMock()
        group_conn.groups = self._gen_openstack_sdk_error()
        group_conn.get_group = self._gen_openstack_sdk_error()
        group_conn.create_group = self._gen_openstack_sdk_error()
        group_conn.delete_group = self._gen_openstack_sdk_error()
        group_conn.update_group = self._gen_openstack_sdk_error()
        self.connection.identity = group_conn
        return self.connection.identity

    def _fake_identity_role(self):
        role_conn = mock.MagicMock()
        role_conn.roles = self._gen_openstack_sdk_error()
        role_conn.get_role = self._gen_openstack_sdk_error()
        role_conn.create_role = self._gen_openstack_sdk_error()
        role_conn.delete_role = self._gen_openstack_sdk_error()
        role_conn.update_role = self._gen_openstack_sdk_error()
        self.connection.identity = role_conn
        return self.connection.identity

    def _fake_identity_project(self):
        project_conn = mock.MagicMock()
        project_conn.projects = self._gen_openstack_sdk_error()
        project_conn.get_project = self._gen_openstack_sdk_error()
        project_conn.create_project = self._gen_openstack_sdk_error()
        project_conn.delete_project = self._gen_openstack_sdk_error()
        project_conn.update_project = self._gen_openstack_sdk_error()
        self.connection.identity = project_conn
        return self.connection.identity

    def _fake_dns(self):
        dns_conn = mock.MagicMock()
        dns_conn.find_zone = self._gen_openstack_sdk_error()
        dns_conn.create_zone = self._gen_openstack_sdk_error()
        dns_conn.delete_zone = self._gen_openstack_sdk_error()
        dns_conn.find_recordset = self._gen_openstack_sdk_error()
        dns_conn.create_recordset = self._gen_openstack_sdk_error()
        dns_conn.delete_recordset = self._gen_openstack_sdk_error()
        self.connection.dns = dns_conn
        return self.connection.dns
