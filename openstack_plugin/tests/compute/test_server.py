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
import openstack.compute.v2.server
import openstack.compute.v2.server_interface
import openstack.compute.v2.flavor
import openstack.compute.v2.volume_attachment
import openstack.compute.v2.keypair
import openstack.image.v2.image
import openstack.network.v2.floating_ip
import openstack.network.v2.port
import openstack.network.v2.security_group
import openstack.exceptions
from cloudify.exceptions import (OperationRetry, NonRecoverableError)
from cloudify.mocks import (
    MockContext,
    MockNodeContext,
    MockNodeInstanceContext,
)


# Local imports
from openstack_plugin.tests.base import OpenStackTestBase
from openstack_plugin.resources.compute import server
from openstack_plugin.resources.network import port
from openstack_plugin.utils import (get_snapshot_name,
                                    generate_attachment_volume_key)
from openstack_plugin.constants import (RESOURCE_ID,
                                        OPENSTACK_NAME_PROPERTY,
                                        OPENSTACK_TYPE_PROPERTY,
                                        FLOATING_IP_OPENSTACK_TYPE,
                                        SECURITY_GROUP_OPENSTACK_TYPE,
                                        VOLUME_OPENSTACK_TYPE,
                                        SERVER_OPENSTACK_TYPE,
                                        NETWORK_OPENSTACK_TYPE,
                                        PORT_OPENSTACK_TYPE,
                                        KEYPAIR_OPENSTACK_TYPE,
                                        SERVER_GROUP_OPENSTACK_TYPE,
                                        NETWORK_NODE_TYPE,
                                        PORT_NODE_TYPE,
                                        KEYPAIR_NODE_TYPE,
                                        VOLUME_NODE_TYPE,
                                        SECURITY_GROUP_NODE_TYPE,
                                        SERVER_GROUP_NODE_TYPE,
                                        SERVER_TASK_DELETE,
                                        SERVER_TASK_START,
                                        SERVER_TASK_STOP,
                                        SERVER_INTERFACE_IDS,
                                        SERVER_TASK_BACKUP_DONE,
                                        SERVER_TASK_RESTORE_STATE,
                                        VOLUME_ATTACHMENT_TASK,
                                        VOLUME_DETACHMENT_TASK,
                                        VOLUME_ATTACHMENT_ID,
                                        SERVER_ACTION_STATUS_DONE,
                                        SERVER_ACTION_STATUS_PENDING,
                                        SERVER_PUBLIC_IP_PROPERTY,
                                        SERVER_IP_PROPERTY)


class CustomMockContext(MockContext):

    def __init__(self, *args, **kwargs):
        super(CustomMockContext, self).__init__(*args, **kwargs)

    @property
    def workflow_id(self):
        return 'workflow'


@mock.patch('openstack.connect')
class ServerTestCase(OpenStackTestBase):

    def setUp(self):
        super(ServerTestCase, self).setUp()
        self.type_hierarchy = ['cloudify.nodes.Root', 'cloudify.nodes.Compute']

    @property
    def node_properties(self):
        properties = super(ServerTestCase, self).node_properties
        properties['os_family'] = 'Linux'
        properties['device_name'] = 'test-device'
        return properties

    @property
    def resource_config(self):
        config = super(ServerTestCase, self).resource_config
        config['flavor_id'] = '4'
        config['image_id'] = 'a95b5509-c122-4c2f-823e-884bb559da12'
        return config

    @mock.patch(
        'openstack_plugin.resources.compute'
        '.server._validate_security_groups_on_ports')
    def test_create(self,
                    mock_validate_security_groups_on_ports,
                    mock_connection):
        # Prepare the context for create operation
        rel_specs = [
            {
                'node': {
                    'id': 'network-1',
                    'properties': {
                        'client_config': self.client_config,
                        'resource_config': {
                            'name': 'test-network',
                        }
                    }
                },
                'instance': {
                    'id': 'network-1-efrgsd',
                    'runtime_properties': {
                        RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe4',
                        OPENSTACK_TYPE_PROPERTY: NETWORK_OPENSTACK_TYPE,
                        OPENSTACK_NAME_PROPERTY: 'test-network'
                    }
                },
                'type': NETWORK_NODE_TYPE,
            },
            {
                'node': {
                    'id': 'port-1',
                    'properties': {
                        'client_config': self.client_config,
                        'resource_config': {
                            'name': 'test-port',
                        }
                    }
                },
                'instance': {
                    'id': 'port-1-efrgsd',
                    'runtime_properties': {
                        RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe2',
                        OPENSTACK_TYPE_PROPERTY: PORT_OPENSTACK_TYPE,
                        OPENSTACK_NAME_PROPERTY: 'test-port'
                    }
                },
                'type': PORT_NODE_TYPE,
            },
            {
                'node': {
                    'id': 'volume-1',
                    'properties': {
                        'client_config': self.client_config,
                        'resource_config': {
                            'name': 'test-volume',
                        }
                    }
                },
                'instance': {
                    'id': 'volume-1-efrgsd',
                    'runtime_properties': {
                        RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe1',
                        OPENSTACK_TYPE_PROPERTY: VOLUME_OPENSTACK_TYPE,
                        OPENSTACK_NAME_PROPERTY: 'test-volume'
                    }
                },
                'type': VOLUME_NODE_TYPE,
            },
            {
                'node': {
                    'id': 'keypair-1',
                    'properties': {
                        'client_config': self.client_config,
                        'resource_config': {
                            'name': 'test-keypair',
                        }
                    }
                },
                'instance': {
                    'id': 'keypair-1-efrgsd',
                    'runtime_properties': {
                        RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe0',
                        OPENSTACK_TYPE_PROPERTY: KEYPAIR_OPENSTACK_TYPE,
                        OPENSTACK_NAME_PROPERTY: 'test-keypair'
                    }
                },
                'type': KEYPAIR_NODE_TYPE,
            },
            {
                'node': {
                    'id': 'server-group-1',
                    'properties': {
                        'client_config': self.client_config,
                        'resource_config': {
                            'name': 'test-server-group',
                        }
                    }
                },
                'instance': {
                    'id': 'server-group-1-efrgsd',
                    'runtime_properties': {
                        RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe9',
                        OPENSTACK_TYPE_PROPERTY: SERVER_GROUP_OPENSTACK_TYPE,
                        OPENSTACK_NAME_PROPERTY: 'test-server-group'
                    }
                },
                'type': SERVER_GROUP_NODE_TYPE,
                'type_hierarchy': [SERVER_GROUP_NODE_TYPE,
                                   'cloudify.nodes.Root']
            },
            {
                'node': {
                    'id': 'security-group-1',
                    'properties': {
                        'client_config': self.client_config,
                        'resource_config': {
                            'name': 'test-security-group',
                        }
                    }
                },
                'instance': {
                    'id': 'security-group-1-efrgs1d',
                    'runtime_properties': {
                        RESOURCE_ID: 'a16b5203-b122-4c2f-823e-884bb559afe9',
                        OPENSTACK_TYPE_PROPERTY: SECURITY_GROUP_OPENSTACK_TYPE,
                        OPENSTACK_NAME_PROPERTY: 'test-security-group'
                    }
                },
                'type': SECURITY_GROUP_NODE_TYPE,
                'type_hierarchy': [SECURITY_GROUP_NODE_TYPE,
                                   'cloudify.nodes.Root']
            }
        ]
        server_rels = self.get_mock_relationship_ctx_for_node(rel_specs)
        # Prepare the context for create operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.create',
            type_hierarchy=self.type_hierarchy,
            test_relationships=server_rels)

        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',

        })

        flavor_instance = openstack.compute.v2.flavor.Flavor(**{
            'id': '4',
            'name': 'test_flavor',
            'links': '2',
            'os-flavor-access:is_public': True,
            'ram': 6,
            'vcpus': 8,
            'swap': 8

        })
        image_instance = openstack.image.v2.image.Image(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559da12',
            'name': 'test-image-name',
            'container_format': 'test_bare',
            'disk_format': 'test_format',
            'checksum': '6d8f1c8cf05e1fbdc8b543fda1a9fa7f',
            'size': 258540032

        })

        mock_validate_security_groups_on_ports.return_value = True
        # Mock get flavor response
        mock_connection().compute.find_flavor = \
            mock.MagicMock(return_value=flavor_instance)

        # Mock get image response
        mock_connection().image.find_image = \
            mock.MagicMock(return_value=image_instance)

        mock_connection().compute.create_server = \
            mock.MagicMock(return_value=server_instance)
        server.create(openstack_resource=None)

        # Check if the resource id is already set or not
        self.assertIn(
            RESOURCE_ID,
            self._ctx.instance.runtime_properties)

        # Check if the server payload is assigned for the created server
        self.assertIn(
            SERVER_OPENSTACK_TYPE,
            self._ctx.instance.runtime_properties)

        # Check to see if there is a "security_groups" runtime property
        self.assertIn(
            'security_groups',
            self._ctx.instance.runtime_properties)

        self.assertIn(
            '__security_groups_link_to_port',
            self._ctx.instance.runtime_properties)

        # Check to see if there is a "security_groups" length is 1
        self.assertEqual(
            len(self._ctx.instance.runtime_properties['security_groups']), 1)

        # Check to see if "__security_groups_link_to_port" is True
        self.assertTrue(
            self._ctx.instance.runtime_properties[
                '__security_groups_link_to_port'
            ])

        # Check to see if there is a "security_groups" length is 1
        self.assertEqual(
            self._ctx.instance.runtime_properties['security_groups'][0]['id'],
            'a16b5203-b122-4c2f-823e-884bb559afe9')

    @mock.patch(
        'openstack_plugin.resources.compute.server'
        '.get_security_groups_from_relationships')
    @mock.patch(
        'openstack_plugin.resources.compute.server._get_security_groups_ids')
    def test_get_security_groups_for_server(self,
                                            mock_get_sg_ids,
                                            mock_get_sgs_from_rel,
                                            _):

        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            test_properties={},
            ctx_operation_name='cloudify.interfaces.lifecycle.create',
            type_hierarchy=self.type_hierarchy)

        mock_get_sg_ids.return_value = [
            {
                'id': 'a95b5509-c143-3d3g-642k-543cc448sdt7'
            },
        ]

        mock_get_sgs_from_rel.return_value = [
            {
                'id': 'b84b5509-c143-3d3g-642k-632hh557feg6'
            },
        ]

        with self.assertRaises(NonRecoverableError):
            server._get_security_groups_config(
                {
                    'security_groups':
                        [
                            {
                                'id': 'a95b5509-c143-3d3g-642k-543cc448sdt7'
                            },
                        ],
                },
                client_config={'foo': 'boo'}
            )

    @mock.patch(
        'openstack_plugin.resources.compute.server'
        '.get_security_groups_from_relationships')
    @mock.patch(
        'openstack_plugin.resources.compute.server._get_security_groups_ids')
    def test_get_security_groups_for_server_with_compat(self,
                                                        mock_get_sg_ids,
                                                        mock_get_sgs_from_rel,
                                                        _):

        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            test_properties={'use_compact_node': True},
            ctx_operation_name='cloudify.interfaces.lifecycle.create',
            type_hierarchy=self.type_hierarchy)

        mock_get_sg_ids.return_value = [
            {
                'id': 'a95b5509-c143-3d3g-642k-543cc448sdt7'
            },
        ]

        mock_get_sgs_from_rel.return_value = [
            {
                'id': 'b84b5509-c143-3d3g-642k-632hh557feg6'
            },
        ]

        security_groups = server._get_security_groups_config(
            {
                'security_groups':
                    [
                        {
                            'id': 'a95b5509-c143-3d3g-642k-543cc448sdt7'
                        },
                    ],
            },
            client_config={'foo': 'boo'}
        )
        self.assertEqual(len(security_groups), 2)

    @mock.patch(
        'openstack_plugin.resources.compute.server._get_network_name')
    def test_create_external_resource(self,
                                      mock_network_name,
                                      mock_connection):
        properties = dict()
        # Enable external resource
        properties['use_external_resource'] = True

        # Add node properties config to this dict
        properties.update(self.node_properties)
        # Reset resource config since we are going to use external resource
        # and do not care about the resource config data
        properties['resource_config'] = {
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8'
        }

        # Prepare the context for create operation
        rel_specs = [
            {
                'node': {
                    'id': 'network-2',
                    'properties': {
                        'client_config': self.client_config,
                        'resource_config': {
                            'name': 'test-network-2',
                        }
                    }
                },
                'instance': {
                    'id': 'network-2-efrgsd',
                    'runtime_properties': {
                        RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe4',
                        OPENSTACK_TYPE_PROPERTY: NETWORK_OPENSTACK_TYPE,
                        OPENSTACK_NAME_PROPERTY: 'test-network-2'
                    }
                },
                'type': NETWORK_NODE_TYPE,
            },
            {
                'node': {
                    'id': 'network-3',
                    'properties': {
                        'client_config': self.client_config,
                        'resource_config': {
                            'name': 'test-network-3',
                        }
                    }
                },
                'instance': {
                    'id': 'network-3-efrgsd',
                    'runtime_properties': {
                        RESOURCE_ID: 'a85b5509-c122-4c2f-823e-884bb559afe4',
                        OPENSTACK_TYPE_PROPERTY: NETWORK_OPENSTACK_TYPE,
                        OPENSTACK_NAME_PROPERTY: 'test-network-3'
                    }
                },
                'type': NETWORK_NODE_TYPE,
            },
            {
                'node': {
                    'id': 'keypair-1',
                    'properties': {
                        'client_config': self.client_config,
                        'resource_config': {
                            'name': 'test-keypair',
                        }
                    }
                },
                'instance': {
                    'id': 'keypair-1-efrgsd',
                    'runtime_properties': {
                        RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe0',
                        OPENSTACK_TYPE_PROPERTY: KEYPAIR_OPENSTACK_TYPE,
                        OPENSTACK_NAME_PROPERTY: 'test-keypair',
                        'use_external_resource': True,
                    }
                },
                'type': KEYPAIR_NODE_TYPE,
            }
        ]
        server_rels = self.get_mock_relationship_ctx_for_node(rel_specs)
        # Prepare the context for create operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.create',
            type_hierarchy=self.type_hierarchy,
            test_properties=properties,
            test_relationships=server_rels,
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8'
            })

        old_server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {
                'network-1': [
                    {
                        'OS-EXT-IPS:type': 'fixed',
                        'addr': '10.1.0.1',
                        'version': 4
                    }
                ]
            },
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test-keypair',
            'networks': [
                {
                    'uuid': 'a75b5509-c122-4c2f-823e-884bb559afe4',
                    'port_id': 'b95b5509-c122-4c2f-823e-884bb559afe4'
                }
            ]
        })

        updated_server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '10.1.0.1',
            'access_ipv6': '',
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test-keypair',
            'addresses': {
                'network-2': [
                    {
                        'OS-EXT-IPS:type': 'fixed',
                        'addr': '10.1.0.1',
                        'version': 4
                    }
                ],
                'network-3': [
                    {
                        'OS-EXT-IPS:type': 'fixed',
                        'addr': '10.2.0.1',
                        'version': 4
                    }
                ],
                'network-1': [
                    {
                        'OS-EXT-IPS:type': 'fixed',
                        'addr': '10.3.0.1',
                        'version': 4
                    }
                ]
            },
            'networks': [
                {
                    'uuid': 'a95b5509-c122-4c2f-823e-884bb559afe4',
                    'port_id': 'b75b5509-c122-4c2f-823e-884bb559afe4'
                },
                {
                    'uuid': 'a85b5509-c122-4c2f-823e-884bb559afe4',
                    'port_id': 'b85b5509-c122-4c2f-823e-884bb559afe4'
                },
                {
                    'uuid': 'a75b5509-c122-4c2f-823e-884bb559afe4',
                    'port_id': 'b95b5509-c122-4c2f-823e-884bb559afe4'
                }
            ]
        })

        net_1_interface = \
            openstack.compute.v2.server_interface.ServerInterface(**{
                'id': 'a75b5509-c122-4c2f-823e-884bb559afb1',
                'net_id': 'a75b5509-c122-4c2f-823e-884bb559afe4',
                'port_id': 'b95b5509-c122-4c2f-823e-884bb559afe4',
                'server_id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            })

        net_2_interface = \
            openstack.compute.v2.server_interface.ServerInterface(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afa5',
                'net_id': 'a95b5509-c122-4c2f-823e-884bb559afe4',
                'port_id': 'b75b5509-c122-4c2f-823e-884bb559afe4',
                'server_id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            })

        net_3_interface = \
            openstack.compute.v2.server_interface.ServerInterface(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afa7',
                'net_id': 'a85b5509-c122-4c2f-823e-884bb559afe4',
                'port_id': 'b85b5509-c122-4c2f-823e-884bb559afe4',
                'server_id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            })

        keypair_instance = openstack.compute.v2.keypair.Keypair(**{
            'id': 'test-keypair',
            'name': 'test-keypair',
            'fingerprint': 'test_fingerprint',

        })

        # Mock keypair response gor get
        mock_connection().compute.find_keypair = \
            mock.MagicMock(return_value=keypair_instance)

        # Mock get operation in two places
        # First one will be when get the server for the first time
        # Second one will be when we update the server with all interfaces
        # Third one will be when set the runtime properties
        # Fourth one will be when set the external resource property
        mock_connection().compute.find_server = \
            mock.MagicMock(side_effect=[old_server_instance,
                                        updated_server_instance,
                                        updated_server_instance,
                                        updated_server_instance])

        # Mock list server interface for already created/attached nics to
        # the server node
        mock_connection().compute.server_interfaces = \
            mock.MagicMock(return_value=[net_1_interface])

        # Mock create server interface operation
        # Create server interface will be called in multiple places
        mock_connection().compute.create_server_interface = \
            mock.MagicMock(side_effect=[net_2_interface, net_3_interface])

        mock_network_name.side_effect = ['network-2', 'network-3', 'network-1']

        server.create(openstack_resource=None)

        # Check if the resource id is already set or not
        self.assertEqual(
            'a95b5509-c122-4c2f-823e-884bb559afe8',
            self._ctx.instance.runtime_properties[RESOURCE_ID])

        # Check if the server payload is assigned for the created server
        self.assertEqual(
            SERVER_OPENSTACK_TYPE,
            self._ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY])

        for interface_id in ['a95b5509-c122-4c2f-823e-884bb559afa5',
                             'a95b5509-c122-4c2f-823e-884bb559afa7']:
            self.assertTrue(
                interface_id in
                self._ctx.instance.runtime_properties[SERVER_INTERFACE_IDS])

        self.assertEqual(
            '10.1.0.1',
            self._ctx.instance.runtime_properties['access_ipv4'])

        self.assertTrue(
            self._ctx.instance.runtime_properties[SERVER_IP_PROPERTY],
            '10.1.0.1')

        self.assertEqual(
            3,
            len(self._ctx.instance.runtime_properties['ipv4_addresses']))

    @mock.patch('openstack_plugin.resources.compute.server'
                '._get_user_password')
    @mock.patch('openstack_plugin.resources.compute.server'
                '._set_server_ips_runtime_properties')
    @mock.patch('openstack_plugin.resources.compute.server'
                '._handle_connect_security_groups_to_server')
    def test_configure(self,
                       mock_handle_security_groups_connection,
                       mock_ips_runtime_properties,
                       mock_user_password,
                       mock_connection):
        # Prepare the context for configure operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            test_runtime_properties={
                'security_groups': [{
                    'id': 'a95b5509-c143-3d3g-642k-543cc448sdt7'
                }]
            },
            ctx_operation_name='cloudify.interfaces.lifecycle.configure',
            type_hierarchy=self.type_hierarchy)
        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',
            'security_groups': [],

        })
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        server.configure(openstack_resource=None)
        mock_ips_runtime_properties.assert_called()
        mock_user_password.assert_called()
        mock_handle_security_groups_connection.assert_called()

    @mock.patch('openstack_plugin.resources.compute.server'
                '._get_user_password')
    @mock.patch('openstack_plugin.resources.compute.server'
                '._set_server_ips_runtime_properties')
    @mock.patch('openstack_sdk.resources.compute.OpenstackServer'
                '.remove_security_group_from_server')
    @mock.patch('openstack_plugin.resources.compute.server'
                '._attach_security_groups_to_server')
    def test_configure_with_attach_security_groups(
            self,
            mock_attach_security_groups_to_server,
            mock_remove_sg_from_server,
            mock_ips_runtime_properties,
            mock_user_password,
            mock_connection
    ):
        # Prepare the context for configure operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            test_runtime_properties={
                'security_groups': [{
                    'id': 'a95b5509-c143-3d3g-642k-543cc448sdt7'
                }],
                '__security_groups_link_to_port': True,
                'server': {
                    'foo': 'foo',
                    'bar': 'bar'
                }
            },
            ctx_operation_name='cloudify.interfaces.lifecycle.configure',
            type_hierarchy=self.type_hierarchy)
        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',
            'security_groups': []

        })

        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        server.configure(openstack_resource=None)
        mock_ips_runtime_properties.assert_called()
        mock_user_password.assert_called()
        mock_remove_sg_from_server.assert_not_called()
        mock_attach_security_groups_to_server.assert_called()

        self.assertIn('security_groups',
                      self._ctx.instance.runtime_properties['server'])
        self.assertEqual(
            self._ctx.instance.runtime_properties['server']['security_groups'],
            [
                {
                    'id': 'a95b5509-c143-3d3g-642k-543cc448sdt7'
                }
            ]
        )

    @mock.patch('openstack_plugin.resources.compute.server'
                '._get_user_password')
    @mock.patch('openstack_plugin.resources.compute.server'
                '._set_server_ips_runtime_properties')
    @mock.patch('openstack_plugin.resources.compute.server'
                '._handle_connect_security_groups_to_server')
    def test_configure_with_retry(self,
                                  mock_handle_security_groups_connection,
                                  mock_ips_runtime_properties,
                                  mock_user_password,
                                  mock_connection):
        # Prepare the context for configure operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.configure',
            type_hierarchy=self.type_hierarchy)
        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'UNKNOWN'

        })
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        with self.assertRaises(OperationRetry):
            server.configure(openstack_resource=None)
            mock_ips_runtime_properties.assert_not_called()
            mock_user_password.assert_not_called()
            mock_handle_security_groups_connection.assert_not_called()

    @mock.patch('openstack_plugin.resources.compute.server'
                '._get_user_password')
    @mock.patch('openstack_plugin.resources.compute.server'
                '._set_server_ips_runtime_properties')
    @mock.patch('openstack_plugin.resources.compute.server'
                '._handle_connect_security_groups_to_server')
    def test_configure_with_error(self,
                                  mock_handle_security_groups_connection,
                                  mock_ips_runtime_properties,
                                  mock_user_password,
                                  mock_connection):
        # Prepare the context for configure operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.configure',
            type_hierarchy=self.type_hierarchy)
        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ERROR'

        })
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        with self.assertRaises(NonRecoverableError):
            server.configure(openstack_resource=None)
            mock_ips_runtime_properties.assert_not_called()
            mock_user_password.assert_not_called()
            mock_handle_security_groups_connection.assert_not_called()

    def test_stop(self, mock_connection):
        # Prepare the context for stop operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.stop',
            type_hierarchy=self.type_hierarchy,
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8'
            })
        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',

        })

        stopped_server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'SHUTOFF',

        })
        # Mock stop operation
        mock_connection().compute.stop_server = \
            mock.MagicMock(return_value=None)

        # Mock find operation
        mock_connection().compute.find_server = \
            mock.MagicMock(side_effect=[server_instance,
                                        stopped_server_instance,
                                        stopped_server_instance])

        # Stop the server
        server.stop(openstack_resource=None)

        # Check if the resource id is already set or not
        self.assertIn(
            SERVER_TASK_STOP,
            self._ctx.instance.runtime_properties)

    @mock.patch('openstack_sdk.resources.compute'
                '.OpenstackServer.delete_server_interface')
    def test_stop_external_resource(self,
                                    mock_delete_server_interface,
                                    mock_connection):

        properties = dict()
        # Enable external resource
        properties['use_external_resource'] = True

        # Add node properties config to this dict
        properties.update(self.node_properties)
        # Reset resource config since we are going to use external resource
        # and do not care about the resource config data
        properties['resource_config'] = {
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8'
        }

        # Prepare the context for stop operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.stop',
            type_hierarchy=self.type_hierarchy,
            test_properties=properties,
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                SERVER_INTERFACE_IDS: [
                    'a95b5509-c122-4c2f-823e-884bb559afe2',
                    'a95b5509-c122-4c2f-823e-884bb559af21'
                ]
            })
        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',

        })

        # Mock find operation
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)
        # Stop the server
        server.stop(openstack_resource=None)

        self.assertEqual(mock_delete_server_interface.call_count, 2)

    def test_reboot(self, mock_connection):
        # Prepare the context for reboot operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.reboot',
            type_hierarchy=self.type_hierarchy,
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8'
            })
        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',

        })

        rebooted_server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'REBOOT',

        })

        # Mock stop operation
        mock_connection().compute.reboot_server = \
            mock.MagicMock(return_value=None)

        # Mock get operation
        mock_connection().compute.find_server = \
            mock.MagicMock(side_effect=[server_instance,
                                        rebooted_server_instance])

        self._ctx.operation.retry = mock.Mock(side_effect=OperationRetry())

        with self.assertRaises(OperationRetry):
            # Reboot the server
            server.reboot(openstack_resource=None)
        self._ctx.operation.retry.assert_called_with(
            message='Server has REBOOT state. Waiting.', retry_after=30)

    def test_suspend(self, mock_connection):
        # Prepare the context for suspend operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            ctx_operation_name='cloudify.interfaces.freeze.suspend',
            type_hierarchy=self.type_hierarchy,
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8'
            })
        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',

        })

        # Mock suspend operation
        mock_connection().compute.suspend_server = \
            mock.MagicMock(return_value=None)

        # Mock find operation
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        # Call suspend
        server.suspend(openstack_resource=None)

    def test_resume(self, mock_connection):
        # Prepare the context for resume operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            ctx_operation_name='cloudify.interfaces.freeze.resume',
            type_hierarchy=self.type_hierarchy,
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8'
            })
        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',

        })

        # Mock resume operation
        mock_connection().compute.resume_server = \
            mock.MagicMock(return_value=None)

        # Mock find operation
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        # Call resume
        server.resume(openstack_resource=None)

    def test_create_snapshot(self, mock_connection):
        # Prepare the context for snapshot create operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            ctx_operation_name='cloudify.interfaces.snapshot.create',
            type_hierarchy=self.type_hierarchy,
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8'
            })
        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',

        })

        # Mock backup operation
        mock_connection().compute.backup = \
            mock.MagicMock(return_value=None)

        # Mock find server operation
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        # Mock list image operation
        mock_connection().image.images = \
            mock.MagicMock(return_value=[])

        # Call snapshot
        snapshot_params = {
            'snapshot_name': 'test-snapshot',
            'snapshot_incremental': False
        }
        server.snapshot_create(**snapshot_params)

        # Check if the resource id is already set or not
        self.assertIn(
            SERVER_TASK_BACKUP_DONE,
            self._ctx.instance.runtime_properties)

    def test_create_backup(self, mock_connection):
        # Prepare the context for backup create operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            ctx_operation_name='cloudify.interfaces.snapshot.create',
            type_hierarchy=self.type_hierarchy,
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8'
            })
        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',

        })

        # Mock backup operation
        mock_connection().compute.create_image = \
            mock.MagicMock(return_value=None)

        # Mock find server operation
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        # Mock list image operation
        mock_connection().image.images = \
            mock.MagicMock(return_value=[])

        # Call snapshot
        snapshot_params = {
            'snapshot_name': 'test-snapshot',
            'snapshot_incremental': True,
            'snapshot_rotation': 2,
            'snapshot_type': 'Daily'
        }
        server.snapshot_create(**snapshot_params)

        # Check if the resource id is already set or not
        self.assertIn(
            SERVER_TASK_BACKUP_DONE,
            self._ctx.instance.runtime_properties)

    def test_apply_snapshot(self,
                            mock_connection):
        # Prepare the context for snapshot apply operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            ctx_operation_name='cloudify.interfaces.snapshot.apply',
            type_hierarchy=self.type_hierarchy,
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8'
            })

        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',

        })
        # Generate the snapshot name for the mocked image
        snapshot_name = get_snapshot_name('vm', 'test-snapshot', False)
        image = openstack.image.v2.image.Image(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
            'name': snapshot_name,
            'container_format': 'test_bare',
            'disk_format': 'test_format',
            'checksum': '6d8f1c8cf05e1fbdc8b543fda1a9fa7f',
            'size': 258540032

        })

        # Mock find project response
        mock_connection().identity.find_project = \
            mock.MagicMock(return_value=self.project_resource)

        # Mock backup operation
        mock_connection().compute.backup = \
            mock.MagicMock(return_value=None)

        # Mock find server operation
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        # Mock list image operation
        mock_connection().image.images = \
            mock.MagicMock(return_value=[image])

        # Set runtime properties for apply snapshot
        self._ctx.instance.runtime_properties[SERVER_TASK_RESTORE_STATE]\
            = SERVER_ACTION_STATUS_PENDING
        self._ctx.instance.runtime_properties[SERVER_TASK_STOP] = \
            SERVER_ACTION_STATUS_DONE
        self._ctx.instance.runtime_properties[SERVER_TASK_START] = \
            SERVER_ACTION_STATUS_DONE

        # Call snapshot
        snapshot_params = {
            'snapshot_name': 'test-snapshot',
            'snapshot_incremental': False
        }
        server.snapshot_apply(**snapshot_params)

    def test_apply_backup(self,
                          mock_connection):
        # Prepare the context for backup apply operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            ctx_operation_name='cloudify.interfaces.snapshot.apply',
            type_hierarchy=self.type_hierarchy,
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8'
            })

        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',

        })

        # Generate the snapshot name for the mocked image
        snapshot_name = get_snapshot_name('vm', 'test-snapshot', True)
        image = openstack.image.v2.image.Image(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
            'name': snapshot_name,
            'container_format': 'test_bare',
            'disk_format': 'test_format',
            'checksum': '6d8f1c8cf05e1fbdc8b543fda1a9fa7f',
            'size': 258540032

        })

        # Mock find project response
        mock_connection().identity.find_project = \
            mock.MagicMock(return_value=self.project_resource)

        # Mock backup operation
        mock_connection().compute.backup = \
            mock.MagicMock(return_value=None)

        # Mock find server operation
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        # Mock list image operation
        mock_connection().image.images = \
            mock.MagicMock(return_value=[image])

        # Set runtime properties for apply snapshot
        self._ctx.instance.runtime_properties[SERVER_TASK_RESTORE_STATE]\
            = SERVER_ACTION_STATUS_PENDING
        self._ctx.instance.runtime_properties[SERVER_TASK_STOP] = \
            SERVER_ACTION_STATUS_DONE
        self._ctx.instance.runtime_properties[SERVER_TASK_START] = \
            SERVER_ACTION_STATUS_DONE

        # Call snapshot
        snapshot_params = {
            'snapshot_name': 'test-snapshot',
            'snapshot_incremental': True
        }
        server.snapshot_apply(**snapshot_params)

    def test_delete_snapshot(self,
                             mock_connection):
        # Prepare the context for snapshot delete operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            ctx_operation_name='cloudify.interfaces.snapshot.delete',
            type_hierarchy=self.type_hierarchy,
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8'
            })
        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',

        })

        # Set runtime properties for snapshot
        self._ctx.instance.runtime_properties[SERVER_TASK_BACKUP_DONE]\
            = SERVER_ACTION_STATUS_DONE
        self._ctx.instance.runtime_properties[SERVER_TASK_RESTORE_STATE]\
            = SERVER_ACTION_STATUS_DONE
        self._ctx.instance.runtime_properties[SERVER_TASK_STOP] = \
            SERVER_ACTION_STATUS_DONE
        self._ctx.instance.runtime_properties[SERVER_TASK_START] = \
            SERVER_ACTION_STATUS_DONE

        # Generate the snapshot name for the mocked image
        snapshot_name = get_snapshot_name('vm', 'test-snapshot', False)
        image = openstack.image.v2.image.Image(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
            'name': snapshot_name,
            'container_format': 'test_bare',
            'disk_format': 'test_format',
            'checksum': '6d8f1c8cf05e1fbdc8b543fda1a9fa7f',
            'size': 258540032

        })
        # Mock find project response
        mock_connection().identity.find_project = \
            mock.MagicMock(return_value=self.project_resource)

        # Mock find server operation
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        # Mock list image operation
        mock_connection().image.images = \
            mock.MagicMock(side_effect=[[image], []])

        # Mock list image operation
        mock_connection().image.delete_image = \
            mock.MagicMock(return_value=None)

        # Call snapshot
        snapshot_params = {
            'snapshot_name': 'test-snapshot',
            'snapshot_incremental': False
        }
        server.snapshot_delete(**snapshot_params)

        for attr in [SERVER_TASK_RESTORE_STATE,
                     SERVER_ACTION_STATUS_DONE,
                     SERVER_TASK_STOP,
                     SERVER_TASK_START]:
            self.assertNotIn(attr, self._ctx.instance.runtime_properties)

    def test_delete_backup(self,
                           mock_connection):
        # Prepare the context for snapshot delete backup
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            ctx_operation_name='cloudify.interfaces.snapshot.delete',
            type_hierarchy=self.type_hierarchy,
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8'
            })
        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',

        })

        # Set runtime properties for snapshot
        self._ctx.instance.runtime_properties[SERVER_TASK_BACKUP_DONE]\
            = SERVER_ACTION_STATUS_DONE
        self._ctx.instance.runtime_properties[SERVER_TASK_RESTORE_STATE]\
            = SERVER_ACTION_STATUS_DONE
        self._ctx.instance.runtime_properties[SERVER_TASK_STOP] = \
            SERVER_ACTION_STATUS_DONE
        self._ctx.instance.runtime_properties[SERVER_TASK_START] = \
            SERVER_ACTION_STATUS_DONE

        # Generate the snapshot name for the mocked image
        snapshot_name = get_snapshot_name('vm', 'test-snapshot', True)
        image = openstack.image.v2.image.Image(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
            'name': snapshot_name,
            'container_format': 'test_bare',
            'disk_format': 'test_format',
            'checksum': '6d8f1c8cf05e1fbdc8b543fda1a9fa7f',
            'size': 258540032

        })

        # Mock find project response
        mock_connection().identity.find_project = \
            mock.MagicMock(return_value=self.project_resource)

        # Mock find server operation
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        # Mock list image operation
        mock_connection().image.images = \
            mock.MagicMock(side_effect=[[image], []])

        # Mock list image operation
        mock_connection().image.delete_image = \
            mock.MagicMock(return_value=None)

        # Call snapshot
        snapshot_params = {
            'snapshot_name': 'test-snapshot',
            'snapshot_incremental': True
        }
        server.snapshot_delete(**snapshot_params)

        for attr in [SERVER_TASK_RESTORE_STATE,
                     SERVER_TASK_BACKUP_DONE,
                     SERVER_TASK_STOP,
                     SERVER_TASK_START]:
            self.assertNotIn(attr, self._ctx.instance.runtime_properties)

    @mock.patch(
        'openstack_plugin.resources.compute.server.wait_until_status')
    def test_attach_volume(self, mock_wait_status, mock_connection):
        target = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='server-1',
                runtime_properties={
                    RESOURCE_ID: '1',
                    OPENSTACK_TYPE_PROPERTY: SERVER_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-server',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        source = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='volume-1',
                runtime_properties={
                    RESOURCE_ID: '1',
                    OPENSTACK_TYPE_PROPERTY: VOLUME_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-volume',
                }),
            'node': MockNodeContext(
                id='2',
                properties={
                    'device_name': 'test',
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '2'
            }})

        volume_attachment = \
            openstack.compute.v2.volume_attachment.VolumeAttachment(**{
                'id': '1',
                'server_id': '1',
                'volume_id': '3',
                'attachment_id': '4',
            })

        attachment_task_key = \
            generate_attachment_volume_key(VOLUME_ATTACHMENT_TASK,
                                           'volume-1', 'server-1')

        attachment_task_id = \
            generate_attachment_volume_key(VOLUME_ATTACHMENT_ID,
                                           'volume-1', 'server-1')

        mock_wait_status.return_value = volume_attachment

        # Mock create volume attachment operation
        mock_connection().compute.create_volume_attachment = \
            mock.MagicMock(return_value=volume_attachment)

        self._pepare_relationship_context_for_operation(
            deployment_id='ServerTest',
            source=source,
            target=target,
            ctx_operation_name='cloudify.interfaces.'
                               'relationship_lifecycle.establish', node_id='1')

        # Call attach volume
        server.attach_volume(openstack_resource=None)

        # Check if the resource id is already set or not
        self.assertIn(
            attachment_task_id,
            self._ctx.target.instance.runtime_properties)

        self.assertNotIn(
            attachment_task_key,
            self._ctx.target.instance.runtime_properties)

    @mock.patch(
        'openstack_plugin.resources.compute.server.wait_until_status')
    def test_attach_external_volume(self, mock_wait_status, mock_connection):
        target = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='server-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe6',
                    OPENSTACK_TYPE_PROPERTY: SERVER_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-server',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config,
                    'use_external_resource': True,
                }
            ), '_context': {
                'node_id': '1'
            }})

        source = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='volume-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe8',
                    OPENSTACK_TYPE_PROPERTY: VOLUME_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-volume',
                }),
            'node': MockNodeContext(
                id='2',
                properties={
                    'device_name': 'test',
                    'client_config': self.client_config,
                    'resource_config': self.resource_config,
                    'use_external_resource': True,
                }
            ), '_context': {
                'node_id': '2'
            }})

        volume_attachments = [
            openstack.compute.v2.volume_attachment.VolumeAttachment(**{
                'id': '1',
                'server_id': 'a95b5509-c122-4c2f-823e-884bb559afe6',
                'volume_id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'attachment_id': '4',
            })
        ]

        # Mock list volumes response
        mock_connection().compute.volume_attachments = \
            mock.MagicMock(return_value=volume_attachments)

        self._pepare_relationship_context_for_operation(
            deployment_id='ServerTest',
            source=source,
            target=target,
            ctx_operation_name='cloudify.interfaces.'
                               'relationship_lifecycle.establish', node_id='1')

        # Call attach volume
        server.attach_volume(openstack_resource=None)
        mock_wait_status.assert_not_called()

    @mock.patch(
        'openstack_plugin.resources.compute.server.wait_until_status')
    def test_detach_volume(self, mock_wait_status, mock_connection):
        attachment_task_id = \
            generate_attachment_volume_key(VOLUME_ATTACHMENT_ID,
                                           'volume-1', 'server-1')

        detachment_task_key = \
            generate_attachment_volume_key(VOLUME_DETACHMENT_TASK,
                                           'volume-1', 'server-1')
        target = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='server-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe8',
                    OPENSTACK_TYPE_PROPERTY: SERVER_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-server',
                    attachment_task_id: '1'
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        source = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='volume-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe7',
                    OPENSTACK_TYPE_PROPERTY: VOLUME_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-volume',
                }),
            'node': MockNodeContext(
                id='2',
                properties={
                    'device_name': 'test',
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '2'
            }})

        volume_attachment = \
            openstack.compute.v2.volume_attachment.VolumeAttachment(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe6',
                'server_id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'volume_id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'attachment_id': 'a95b5509-c122-4c2f-823e-884bb559afe3',
            })

        mock_wait_status.return_value = volume_attachment

        # Mock delete volume attachment operation
        mock_connection().compute.delete_volume_attachment = \
            mock.MagicMock(return_value=None)

        self._pepare_relationship_context_for_operation(
            deployment_id='ServerTest',
            source=source,
            target=target,
            ctx_operation_name='cloudify.interfaces.'
                               'relationship_lifecycle.unlink', node_id='1'
        )

        # Call detach volume
        server.detach_volume(openstack_resource=None)

        self.assertNotIn(
            detachment_task_key,
            self._ctx.target.instance.runtime_properties)

    @mock.patch(
        'openstack_plugin.resources.compute.server.wait_until_status')
    def test_detach_external_volume(self, mock_wait_status, mock_connection):
        target = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='server-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe8',
                    OPENSTACK_TYPE_PROPERTY: SERVER_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-server',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config,
                    'use_external_resource': True,
                }
            ), '_context': {
                'node_id': '1'
            }})

        source = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='volume-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe7',
                    OPENSTACK_TYPE_PROPERTY: VOLUME_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-volume',
                }),
            'node': MockNodeContext(
                id='2',
                properties={
                    'device_name': 'test',
                    'client_config': self.client_config,
                    'resource_config': self.resource_config,
                    'use_external_resource': True,
                }
            ), '_context': {
                'node_id': '2'
            }})

        self._pepare_relationship_context_for_operation(
            deployment_id='ServerTest',
            source=source,
            target=target,
            ctx_operation_name='cloudify.interfaces.'
                               'relationship_lifecycle.unlink', node_id='1'
        )

        # Call detach volume
        server.detach_volume(openstack_resource=None)
        mock_wait_status.assert_not_called()

    def test_connect_floating_ip(self, mock_connection):
        target = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='floating-ip-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe2',
                    OPENSTACK_TYPE_PROPERTY: FLOATING_IP_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-floating-ip',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        source = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='server-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe8',
                    OPENSTACK_TYPE_PROPERTY: SERVER_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-server',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        # Mock add floating ip to server operation
        mock_connection().compute.add_floating_ip_to_server = \
            mock.MagicMock(return_value=None)

        self._pepare_relationship_context_for_operation(
            deployment_id='ServerTest',
            source=source,
            target=target,
            ctx_operation_name='cloudify.interfaces.'
                               'relationship_lifecycle.establish', node_id='1')

        # Call connect floating ip
        server.connect_floating_ip(floating_ip='10.2.3.4',
                                   openstack_resource=None)

    def test_connect_external_floating_ip(self, mock_connection):
        target = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='floating-ip-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe2',
                    OPENSTACK_TYPE_PROPERTY: FLOATING_IP_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-floating-ip',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config,
                    'use_external_resource': True,
                }
            ), '_context': {
                'node_id': '1'
            }})

        source = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='server-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe8',
                    OPENSTACK_TYPE_PROPERTY: SERVER_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-server',
                    'public_ip_address': '10.2.3.4'
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config,
                    'use_external_resource': True,
                }
            ), '_context': {
                'node_id': '1'
            }})

        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '10.2.3.4',
            'access_ipv6': '',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',

        })

        floating_ip_instance = openstack.network.v2.floating_ip.FloatingIP(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe2',
            'description': 'test_description',
            'name': '10.2.3.4',
            'created_at': '2016-03-09T12:14:57.233772',
            'fixed_ip_address': '',
            'floating_ip_address': '10.2.3.4',
            'floating_network_id': '3',
            'port_id': '5',
            'qos_policy_id': '51',
            'tenant_id': '6',
            'router_id': '7',
            'dns_domain': '9',
            'dns_name': '10',
            'status': 'ACTIVE',
            'revision_number': 12,
            'updated_at': '2016-07-09T12:14:57.233772',
            'subnet_id': '14',
            'tags': ['15', '16']

        })

        # Mock find server operation
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        # Mock get floating ip response
        mock_connection().network.get_ip = \
            mock.MagicMock(return_value=floating_ip_instance)

        # Mock find project response
        mock_connection().identity.find_project = \
            mock.MagicMock(return_value=self.project_resource)

        self._pepare_relationship_context_for_operation(
            deployment_id='ServerTest',
            source=source,
            target=target,
            ctx_operation_name='cloudify.interfaces.'
                               'relationship_lifecycle.establish', node_id='1')

        # Call connect floating ip
        server.connect_floating_ip(floating_ip='10.2.3.4',
                                   openstack_resource=None)

    def test_disconnect_floating_ip(self, mock_connection):
        target = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='floating-ip-1',
                runtime_properties={
                    RESOURCE_ID: '10.2.3.4',
                    OPENSTACK_TYPE_PROPERTY: FLOATING_IP_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-floating-ip',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        source = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='server-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe8',
                    OPENSTACK_TYPE_PROPERTY: SERVER_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-server',
                    SERVER_PUBLIC_IP_PROPERTY: '10.2.3.4',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '10.2.3.4',
            'access_ipv6': '',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',

        })

        # Mock find server operation
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        # Mock remove floating ip from server operation
        mock_connection().compute.remove_floating_ip_from_server = \
            mock.MagicMock(return_value=None)

        self._pepare_relationship_context_for_operation(
            deployment_id='ServerTest',
            source=source,
            target=target,
            ctx_operation_name='cloudify.interfaces.'
                               'relationship_lifecycle.unlink', node_id='1')

        # Trigger disconnect floating ip
        server.disconnect_floating_ip(floating_ip='10.2.3.4',
                                      openstack_resource=None)

    def test_disconnect_external_floating_ip(self, mock_connection):
        target = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='floating-ip-1',
                runtime_properties={
                    RESOURCE_ID: '10.2.3.4',
                    OPENSTACK_TYPE_PROPERTY: FLOATING_IP_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-floating-ip',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config,
                    'use_external_resource': True,
                }
            ), '_context': {
                'node_id': '2'
            }})

        source = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='server-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe8',
                    OPENSTACK_TYPE_PROPERTY: SERVER_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-server',
                    SERVER_PUBLIC_IP_PROPERTY: '10.2.3.4',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config,
                    'use_external_resource': True,
                }
            ), '_context': {
                'node_id': '1'
            }})

        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '10.2.3.4',
            'access_ipv6': '',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',
        })

        # Mock find server operation
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        self._pepare_relationship_context_for_operation(
            deployment_id='ServerTest',
            source=source,
            target=target,
            ctx_operation_name='cloudify.interfaces.'
                               'relationship_lifecycle.unlink', node_id='1')

        # Call disconnect floating ip
        server.disconnect_floating_ip(floating_ip='10.2.3.4',
                                      openstack_resource=None)

    @mock.patch('openstack_sdk.resources.compute.OpenstackServer'
                '.add_security_group_to_server')
    def test_connect_security_group(self,
                                    mock_add_security_group_to_server,
                                    mock_connection):
        target = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='security-group-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe7',
                    OPENSTACK_TYPE_PROPERTY: SECURITY_GROUP_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-security-group',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        source = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='server-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe8',
                    OPENSTACK_TYPE_PROPERTY: SERVER_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-server',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '10.2.3.4',
            'access_ipv6': '',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',
            'security_groups': [
                {
                    'name': 'node-security-group'
                }
            ]
        })
        security_group_instance = \
            openstack.network.v2.security_group.SecurityGroup(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': 'node-security-group',
                'created_at': '2016-10-04T12:14:57.233772',
                'description': '1',
                'revision_number': 3,
                'tenant_id': '4',
                'updated_at': '2016-10-14T12:16:57.233772',
            })

        # Mock find server operation
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        # Mock security group instance
        mock_connection().network.get_security_group = \
            mock.MagicMock(return_value=security_group_instance)

        self._pepare_relationship_context_for_operation(
            deployment_id='ServerTest',
            source=source,
            target=target,
            ctx_operation_name='cloudify.interfaces.'
                               'relationship_lifecycle.establish', node_id='1')

        # Call connect security group
        server.connect_security_group(
            security_group_id='a95b5509-c122-4c2f-823e-884bb559afe7',
            openstack_resource=None
        )
        mock_add_security_group_to_server.assert_not_called()

    @mock.patch(
        'openstack_sdk.resources.compute'
        '.OpenstackServer.add_security_group_to_server')
    def test_connect_external_security_group(self,
                                             mock_add_sg,
                                             mock_connection):
        target = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='security-group-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe7',
                    OPENSTACK_TYPE_PROPERTY: SECURITY_GROUP_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-security-group',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config,
                    'use_external_resource': True,
                }
            ), '_context': {
                'node_id': '1'
            }})

        source = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='server-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe8',
                    OPENSTACK_TYPE_PROPERTY: SERVER_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-server',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config,
                    'use_external_resource': True,
                }
            ), '_context': {
                'node_id': '1'
            }})

        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '10.2.3.4',
            'access_ipv6': '',
            'addresses': {},
            'security_groups': [{'name': 'node-security-group'}],
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',

        })

        # Mock find server operation
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        self._pepare_relationship_context_for_operation(
            deployment_id='ServerTest',
            source=source,
            target=target,
            ctx_operation_name='cloudify.interfaces.'
                               'relationship_lifecycle.establish', node_id='1')

        # Call connect security group
        server.connect_security_group(
            security_group_id='a95b5509-c122-4c2f-823e-884bb559afe7',
            openstack_resource=None
        )
        mock_add_sg.assert_not_called()

    @mock.patch(
        'openstack_plugin.resources.compute.'
        'server._disconnect_security_group_from_server_ports')
    @mock.patch(
        'openstack_sdk.resources.compute.'
        'OpenstackServer.remove_security_group_from_server')
    def test_disconnect_security_group(self,
                                       mock_remove_security_group,
                                       mock_clean_ports,
                                       mock_connection):
        target = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='security-group-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe7',
                    OPENSTACK_TYPE_PROPERTY: SECURITY_GROUP_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-security-group',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        source = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='server-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe8',
                    OPENSTACK_TYPE_PROPERTY: SERVER_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-server',
                    'server': {
                        'name': 'test',
                        'security_groups': [
                            {
                                'id': 'a95b5509-c122-4c2f-823e-884bb559afe5'
                            },
                            {
                                'id': 'a95b5509-c122-4c2f-823e-884bb559afe4'
                            }
                        ]
                    }
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '10.2.3.4',
            'access_ipv6': '',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',
            'security_groups': [
                {
                    'name': 'sg-1'
                },
                {
                    'name': 'sg-2'
                }
            ]
        })
        ports = [
            openstack.network.v2.port.Port(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe1',
                'name': 'test_port_1',
                'admin_state_up': True,
                'device_id': '9',
                'security_groups': [
                    {
                        'id': 'a95b5509-c122-4c2f-823e-884bb559afe5'
                    },
                    {
                        'id': 'a95b5509-c122-4c2f-823e-884bb559afe4'
                    }
                ]
            }),
            openstack.network.v2.port.Port(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe2',
                'name': 'test_port_2',
                'admin_state_up': True,
                'device_id': '9',
                'security_groups': [
                    {
                        'id': 'a95b5509-c122-4c2f-823e-884bb559afe5'
                    },
                    {
                        'id': 'a95b5509-c122-4c2f-823e-884bb559afe4'
                    }
                ]
            }),
        ]

        # Mock list port response
        mock_connection().network.ports = mock.MagicMock(return_value=ports)

        # Mock find server operation
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        self._pepare_relationship_context_for_operation(
            deployment_id='ServerTest',
            source=source,
            target=target,
            ctx_operation_name='cloudify.interfaces.'
                               'relationship_lifecycle.unlink', node_id='1')

        # Call disconnect security group
        server.disconnect_security_group(
            security_group_id='a95b5509-c122-4c2f-823e-884bb559afe7',
            openstack_resource=None)
        mock_clean_ports.assert_called()
        mock_remove_security_group.assert_called()

    @mock.patch(
        'openstack_plugin.resources.compute.'
        'server._disconnect_security_group_from_server_ports')
    def test_disconnect_external_security_group(self,
                                                mock_clean_ports,
                                                mock_connection):
        target = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='security-group-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe7',
                    OPENSTACK_TYPE_PROPERTY: SECURITY_GROUP_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-security-group',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config,
                    'use_external_resource': True,
                }
            ), '_context': {
                'node_id': '1'
            }})

        source = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='server-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe8',
                    OPENSTACK_TYPE_PROPERTY: SERVER_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-server',
                    'server': {
                        'name': 'test',
                        'security_groups': [
                            {
                                'id': 'a95b5509-c122-4c2f-823e-884bb559afe5'
                            },
                            {
                                'id': 'a95b5509-c122-4c2f-823e-884bb559afe4'
                            }
                        ]
                    }
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config,
                    'use_external_resource': True,
                }
            ), '_context': {
                'node_id': '1'
            }})

        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '10.2.3.4',
            'access_ipv6': '',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',

        })

        # Mock find server operation
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        self._pepare_relationship_context_for_operation(
            deployment_id='ServerTest',
            source=source,
            target=target,
            ctx_operation_name='cloudify.interfaces.'
                               'relationship_lifecycle.unlink', node_id='1')

        # Call disconnect security group
        server.disconnect_security_group(
            security_group_id='a95b5509-c122-4c2f-823e-884bb559afe7',
            openstack_resource=None)
        mock_clean_ports.assert_not_called()

    def test_attach_port(self, mock_connection):
        target = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='port-1',
                runtime_properties={
                    RESOURCE_ID: 'a75b5509-c122-4c2f-823e-884bb559afe2',
                    OPENSTACK_TYPE_PROPERTY: PORT_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-port',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        source = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='server-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe8',
                    OPENSTACK_TYPE_PROPERTY: SERVER_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-server',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'server-1',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',

        })

        old_port_instance = openstack.network.v2.port.Port(**{
            'id': 'a75b5509-c122-4c2f-823e-884bb559afe2',
            'name': 'a75b5509-c122-4c2f-823e-884bb559afe2',
            'admin_state_up': True,
            'binding_host_id': '3',
            'binding_profile': {'4': 4},
            'binding_vif_details': {'5': 5},
            'binding_vif_type': '6',
            'binding_vnic_type': '7',
            'created_at': '2016-03-09T12:14:57.233772',
            'data_plane_status': '32',
            'description': 'port_description',
            'device_id': None,
            'device_owner': '10',
            'dns_assignment': [{'11': 11}],
            'dns_domain': 'a11',
            'dns_name': '12',
            'extra_dhcp_opts': [{'13': 13}],
            'mac_address': '00-14-22-01-23-45',
            'network_id': '18',
            'port_security_enabled': True,
            'qos_policy_id': '21',
            'revision_number': 22,
            'security_groups': ['23'],
            'status': '25',
            'tenant_id': '26',
            'updated_at': '2016-07-09T12:14:57.233772',
        })

        new_port_instance = openstack.network.v2.port.Port(**{
            'id': 'a75b5509-c122-4c2f-823e-884bb559afe2',
            'name': 'a75b5509-c122-4c2f-823e-884bb559afe2',
            'admin_state_up': True,
            'binding_host_id': '3',
            'binding_profile': {'4': 4},
            'binding_vif_details': {'5': 5},
            'binding_vif_type': '6',
            'binding_vnic_type': '7',
            'created_at': '2016-03-09T12:14:57.233772',
            'data_plane_status': '32',
            'description': 'port_description',
            'device_id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'device_owner': '10',
            'dns_assignment': [{'11': 11}],
            'dns_domain': 'a11',
            'dns_name': '12',
            'extra_dhcp_opts': [{'13': 13}],
            'mac_address': '00-14-22-01-23-45',
            'network_id': '18',
            'port_security_enabled': True,
            'qos_policy_id': '21',
            'revision_number': 22,
            'security_groups': ['23'],
            'status': '25',
            'tenant_id': '26',
            'updated_at': '2016-07-09T12:14:57.233772',
        })

        # Mock get port response
        mock_connection().network.get_port = \
            mock.MagicMock(return_value=old_port_instance)

        # Mock update port response
        mock_connection().network.update_port = \
            mock.MagicMock(return_value=new_port_instance)

        # Mock get server response
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        self._pepare_relationship_context_for_operation(
            deployment_id='ServerTest',
            source=source,
            target=target,
            ctx_operation_name='cloudify.interfaces.'
                               'relationship_lifecycle.establish', node_id='1')

        # Call attach port to server
        port.attach(port_id='a95b5509-c122-4c2f-823e-884bb559afe2',
                    openstack_resource=None)

    def test_detach_port(self, mock_connection):
        target = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='port-1',
                runtime_properties={
                    RESOURCE_ID: 'a75b5509-c122-4c2f-823e-884bb559afe2',
                    OPENSTACK_TYPE_PROPERTY: PORT_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-port',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        source = CustomMockContext({
            'instance': MockNodeInstanceContext(
                id='server-1',
                runtime_properties={
                    RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe8',
                    OPENSTACK_TYPE_PROPERTY: SERVER_OPENSTACK_TYPE,
                    OPENSTACK_NAME_PROPERTY: 'node-server',
                }),
            'node': MockNodeContext(
                id='1',
                properties={
                    'client_config': self.client_config,
                    'resource_config': self.resource_config
                }
            ), '_context': {
                'node_id': '1'
            }})

        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'server-1',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',

        })

        old_port_instance = openstack.network.v2.port.Port(**{
            'id': 'a75b5509-c122-4c2f-823e-884bb559afe2',
            'name': 'a75b5509-c122-4c2f-823e-884bb559afe2',
            'admin_state_up': True,
            'binding_host_id': '3',
            'binding_profile': {'4': 4},
            'binding_vif_details': {'5': 5},
            'binding_vif_type': '6',
            'binding_vnic_type': '7',
            'created_at': '2016-03-09T12:14:57.233772',
            'data_plane_status': '32',
            'description': 'port_description',
            'device_id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'device_owner': '10',
            'dns_assignment': [{'11': 11}],
            'dns_domain': 'a11',
            'dns_name': '12',
            'extra_dhcp_opts': [{'13': 13}],
            'mac_address': '00-14-22-01-23-45',
            'network_id': '18',
            'port_security_enabled': True,
            'qos_policy_id': '21',
            'revision_number': 22,
            'security_groups': ['23'],
            'status': '25',
            'tenant_id': '26',
            'updated_at': '2016-07-09T12:14:57.233772',
        })

        new_port_instance = openstack.network.v2.port.Port(**{
            'id': 'a75b5509-c122-4c2f-823e-884bb559afe2',
            'name': 'a75b5509-c122-4c2f-823e-884bb559afe2',
            'admin_state_up': True,
            'binding_host_id': '3',
            'binding_profile': {'4': 4},
            'binding_vif_details': {'5': 5},
            'binding_vif_type': '6',
            'binding_vnic_type': '7',
            'created_at': '2016-03-09T12:14:57.233772',
            'data_plane_status': '32',
            'description': 'port_description',
            'device_id': None,
            'device_owner': '10',
            'dns_assignment': [{'11': 11}],
            'dns_domain': 'a11',
            'dns_name': '12',
            'extra_dhcp_opts': [{'13': 13}],
            'mac_address': '00-14-22-01-23-45',
            'network_id': '18',
            'port_security_enabled': True,
            'qos_policy_id': '21',
            'revision_number': 22,
            'security_groups': ['23'],
            'status': '25',
            'tenant_id': '26',
            'updated_at': '2016-07-09T12:14:57.233772',
        })

        # Mock get port response
        mock_connection().network.get_port = \
            mock.MagicMock(return_value=old_port_instance)

        # Mock update port response
        mock_connection().network.update_port = \
            mock.MagicMock(return_value=new_port_instance)

        # Mock get server response
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        self._pepare_relationship_context_for_operation(
            deployment_id='ServerTest',
            source=source,
            target=target,
            ctx_operation_name='cloudify.interfaces.'
                               'relationship_lifecycle.unlink', node_id='1')

        # Call detach port
        port.detach(port_id='a95b5509-c122-4c2f-823e-884bb559afe2',
                    openstack_resource=None)

    def test_delete_with_retry(self, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.delete',
            type_hierarchy=self.type_hierarchy,
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8'
            })
        server_instance = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
            'status': 'ACTIVE',

        })
        # Mock delete operation
        mock_connection().compute.delete_server = \
            mock.MagicMock(return_value=None)

        # Mock find operation
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=server_instance)

        # Call delete server operation
        with self.assertRaises(OperationRetry):
            server.delete(openstack_resource=None)
            # Check if the resource id is already set or not
            self.assertIn(
                SERVER_TASK_DELETE,
                self._ctx.instance.runtime_properties)

    def test_delete_with_success(self, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.delete',
            type_hierarchy=self.type_hierarchy,
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                SERVER_TASK_DELETE: True,
            })

        # Mock get operation
        mock_connection().compute.find_server = \
            mock.MagicMock(side_effect=openstack.exceptions.ResourceNotFound)

        server.delete(openstack_resource=None)

    def test_delete_with_error(self, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.delete',
            type_hierarchy=self.type_hierarchy,
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8'
            })

        # Mock find operation
        mock_connection().compute.find_server = \
            mock.MagicMock(side_effect=[openstack.exceptions.ResourceNotFound])

        with self.assertRaises(NonRecoverableError):
            server.delete(openstack_resource=None)

    def test_update(self, mock_connection):
        # Prepare the context for update operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            ctx_operation_name='cloudify.interfaces.operations.update',
            type_hierarchy=self.type_hierarchy,
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8'
            })
        old_server = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
        })

        new_config = {
            'name': 'update_test_server',
        }

        new_server = openstack.compute.v2.server.Server(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
            'name': 'update_test_server',
            'access_ipv4': '1',
            'access_ipv6': '2',
            'addresses': {},
            'config_drive': True,
            'created': '2015-03-09T12:14:57.233772',
            'flavor_id': '2',
            'image_id': '3',
            'availability_zone': 'test_availability_zone',
            'key_name': 'test_key_name',
        })
        mock_connection().compute.find_server = \
            mock.MagicMock(return_value=old_server)
        mock_connection().compute.update_server = \
            mock.MagicMock(return_value=new_server)

        server.update(args=new_config, openstack_resource=None)

        # Check if the server payload is assigned for the created server
        self.assertIn(
            SERVER_OPENSTACK_TYPE,
            self._ctx.instance.runtime_properties)

        # Compare old name value against updated name
        self.assertNotEqual(
            self._ctx.instance.runtime_properties[SERVER_OPENSTACK_TYPE][
                'name'], old_server.name)

    def test_list_servers(self, mock_connection):
        # Prepare the context for list servers operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            ctx_operation_name='cloudify.interfaces.operations.list',
            type_hierarchy=self.type_hierarchy)
        server_list = [
            openstack.compute.v2.server.ServerDetail(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_server_1',
                'access_ipv4': '1',
                'access_ipv6': '2',
                'addresses': {},
                'config_drive': True,
                'created': '2015-03-09T12:14:57.233772',
                'flavor_id': '2',
                'image_id': '3',
                'availability_zone': 'test_availability_zone',
                'key_name': 'test_key_name',
            }),
            openstack.compute.v2.server.ServerDetail(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': 'test_server_2',
                'access_ipv4': '1',
                'access_ipv6': '2',
                'addresses': {},
                'config_drive': True,
                'created': '2015-03-09T12:14:57.233772',
                'flavor_id': '2',
                'image_id': '3',
                'availability_zone': 'test_availability_zone',
                'key_name': 'test_key_name',
            }),
        ]

        mock_connection().compute.servers = \
            mock.MagicMock(return_value=server_list)

        # Call list servers
        server.list_servers(openstack_resource=None)

        # Check if the server list saved as runtime properties
        self.assertIn(
            'server_list',
            self._ctx.instance.runtime_properties)

        # Check the size of server list
        self.assertEqual(
            len(self._ctx.instance.runtime_properties['server_list']), 2)

    @mock.patch('openstack_plugin.resources.compute.server'
                '._get_flavor_or_image_from_server')
    @mock.patch('openstack_sdk.common.OpenstackResource.get_quota_sets')
    def test_creation_validation(self,
                                 mock_quota_sets,
                                 mock_flavor_id,
                                 mock_connection):
        mock_flavor_id.return_value = '4'
        # Prepare the context for creation validation servers operation
        self._prepare_context_for_operation(
            test_name='ServerTestCase',
            ctx_operation_name='cloudify.interfaces.validation.creation',
            type_hierarchy=self.type_hierarchy)
        server_list = [
            openstack.compute.v2.server.ServerDetail(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe8',
                'name': 'test_server_1',
                'access_ipv4': '1',
                'access_ipv6': '2',
                'addresses': {},
                'config_drive': True,
                'created': '2015-03-09T12:14:57.233772',
                'flavor_id': '2',
                'image_id': '3',
                'availability_zone': 'test_availability_zone',
                'key_name': 'test_key_name',
            }),
            openstack.compute.v2.server.ServerDetail(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe7',
                'name': 'test_server_2',
                'access_ipv4': '1',
                'access_ipv6': '2',
                'addresses': {'region': '3'},
                'config_drive': True,
                'created': '2015-03-09T12:14:57.233772',
                'flavor_id': '2',
                'image_id': '3',
                'availability_zone': 'test_availability_zone',
                'key_name': 'test_key_name',
            }),
        ]

        # Mock the server list API
        mock_connection().compute.servers = \
            mock.MagicMock(return_value=server_list)

        # Mock the quota size response
        mock_quota_sets.return_value = 20

        # Call creation validation
        server.creation_validation(openstack_resource=None)
