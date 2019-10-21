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
import openstack.network.v2.port

# Local imports
from openstack_plugin.tests.base import OpenStackTestBase
from openstack_plugin.resources.network import port
from openstack_plugin.constants import (RESOURCE_ID,
                                        OPENSTACK_NAME_PROPERTY,
                                        OPENSTACK_TYPE_PROPERTY,
                                        PORT_OPENSTACK_TYPE,
                                        NETWORK_OPENSTACK_TYPE,
                                        SECURITY_GROUP_OPENSTACK_TYPE,
                                        NETWORK_NODE_TYPE,
                                        SECURITY_GROUP_NODE_TYPE)


@mock.patch('openstack.connect')
class PortTestCase(OpenStackTestBase):

    def setUp(self):
        super(PortTestCase, self).setUp()

    @property
    def resource_config(self):
        return {
            'name': 'test_port',
            'description': 'port_description',
        }

    def test_create(self, mock_connection):
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
                    'id': 'security-group-1',
                    'properties': {
                        'client_config': self.client_config,
                        'resource_config': {
                            'name': 'test-security-group',
                        }
                    }
                },
                'instance': {
                    'id': 'security-group-1-efrgsd',
                    'runtime_properties': {
                        RESOURCE_ID: 'a95b5509-c122-4c2f-823e-884bb559afe2',
                        OPENSTACK_TYPE_PROPERTY: SECURITY_GROUP_OPENSTACK_TYPE,
                        OPENSTACK_NAME_PROPERTY: 'test-security-group'
                    }
                },
                'type': SECURITY_GROUP_NODE_TYPE,
            }
        ]

        port_rels = self.get_mock_relationship_ctx_for_node(rel_specs)
        self._prepare_context_for_operation(
            test_name='PortTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.create',
            test_relationships=port_rels)

        port_instance = openstack.network.v2.port.Port(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe1',
            'name': 'test_port',
            'admin_state_up': True,
            'binding_host_id': '3',
            'binding_profile': {'4': 4},
            'binding_vif_details': {'5': 5},
            'binding_vif_type': '6',
            'binding_vnic_type': '7',
            'created_at': '2016-03-09T12:14:57.233772',
            'data_plane_status': '32',
            'description': 'port_description',
            'device_id': '9',
            'device_owner': '10',
            'dns_assignment': [{'11': 11}],
            'dns_domain': 'a11',
            'dns_name': '12',
            'extra_dhcp_opts': [{'13': 13}],
            'fixed_ips': [
                {
                    'ip_address': '10.0.0.1'
                },
                {
                    'ip_address': '10.0.0.2'
                }
            ],
            'allowed_address_pairs':
                [
                    {
                        'ip_address': '10.0.0.3'
                    },
                    {
                        'ip_address': '10.0.0.4'
                    }
                ],
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
        # Mock create port response
        mock_connection().network.create_port = \
            mock.MagicMock(return_value=port_instance)

        # Call create port
        port.create()

        self.assertEqual(self._ctx.instance.runtime_properties[RESOURCE_ID],
                         'a95b5509-c122-4c2f-823e-884bb559afe1')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY],
            'test_port')

        self.assertEqual(
            self._ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY],
            PORT_OPENSTACK_TYPE)

        self.assertEqual(
            self._ctx.instance.runtime_properties['fixed_ips'],
            ['10.0.0.1', '10.0.0.2'])

        self.assertEqual(
            self._ctx.instance.runtime_properties['ipv4_addresses'],
            ['10.0.0.1', '10.0.0.2'])

        self.assertEqual(
            self._ctx.instance.runtime_properties['ipv4_address'], '')

        self.assertEqual(
            self._ctx.instance.runtime_properties['ipv6_addresses'], [])

        self.assertEqual(
            self._ctx.instance.runtime_properties['ipv6_address'], '')

        self.assertEqual(
            self._ctx.instance.runtime_properties['mac_address'],
            '00-14-22-01-23-45')

        self.assertEqual(
            self._ctx.instance.runtime_properties['allowed_address_pairs'],
            [{'ip_address': '10.0.0.3'}, {'ip_address': '10.0.0.4'}])

    def test_delete(self, mock_connection):
        # Prepare the context for delete operation
        self._prepare_context_for_operation(
            test_name='PortTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.delete')

        port_instance = openstack.network.v2.port.Port(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe1',
            'name': 'test_port',
            'admin_state_up': True,
            'binding_host_id': '3',
            'binding_profile': {'4': 4},
            'binding_vif_details': {'5': 5},
            'binding_vif_type': '6',
            'binding_vnic_type': '7',
            'created_at': '2016-03-09T12:14:57.233772',
            'data_plane_status': '32',
            'description': 'port_description',
            'device_id': '9',
            'device_owner': '10',
            'dns_assignment': [{'11': 11}],
            'dns_domain': 'a11',
            'dns_name': '12',
            'extra_dhcp_opts': [{'13': 13}],
            'fixed_ips': [{'10.0.0.1': '10.0.0.2'}],
            'allowed_address_pairs':
                [
                    {
                        'ip_address': '10.0.0.3'
                    },
                    {
                        'ip_address': '10.0.0.4'
                    }
                ],
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
        # Mock delete port response
        mock_connection().network.delete_port = \
            mock.MagicMock(return_value=None)

        # Mock get port response
        mock_connection().network.get_port = \
            mock.MagicMock(return_value=port_instance)

        # Call delete port
        port.delete()

        for attr in [RESOURCE_ID,
                     OPENSTACK_NAME_PROPERTY,
                     OPENSTACK_TYPE_PROPERTY,
                     'fixed_ips',
                     'mac_address',
                     'allowed_address_pairs']:
            self.assertNotIn(attr, self._ctx.instance.runtime_properties)

    def test_update(self, mock_connection):
        # Prepare the context for update operation
        self._prepare_context_for_operation(
            test_name='PortTestCase',
            ctx_operation_name='cloudify.interfaces.operations.update')

        old_port_instance = openstack.network.v2.port.Port(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe1',
            'name': 'test_port',
            'admin_state_up': True,
            'binding_host_id': '3',
            'binding_profile': {'4': 4},
            'binding_vif_details': {'5': 5},
            'binding_vif_type': '6',
            'binding_vnic_type': '7',
            'created_at': '2016-03-09T12:14:57.233772',
            'data_plane_status': '32',
            'description': 'port_description',
            'device_id': '9',
            'device_owner': '10',
            'dns_assignment': [{'11': 11}],
            'dns_domain': 'a11',
            'dns_name': '12',
            'extra_dhcp_opts': [{'13': 13}],
            'fixed_ips': [{'10.0.0.1': '10.0.0.2'}],
            'allowed_address_pairs':
                [
                    {
                        'ip_address': '10.0.0.3'
                    },
                    {
                        'ip_address': '10.0.0.4'
                    }
                ],
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

        new_config = {
            'name': 'test_updated_port',
        }

        new_port_instance = \
            openstack.network.v2.port.Port(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe1',
                'name': 'test_port',
                'admin_state_up': True,
                'binding_host_id': '3',
                'binding_profile': {'4': 4},
                'binding_vif_details': {'5': 5},
                'binding_vif_type': '6',
                'binding_vnic_type': '7',
                'created_at': '2016-03-09T12:14:57.233772',
                'data_plane_status': '32',
                'description': 'port_description',
                'device_id': '9',
                'device_owner': '10',
                'dns_assignment': [{'11': 11}],
                'dns_domain': 'a11',
                'dns_name': '12',
                'extra_dhcp_opts': [{'13': 13}],
                'fixed_ips': [{'10.0.0.1': '10.0.0.2'}],
                'allowed_address_pairs':
                    [
                        {
                            'ip_address': '10.0.0.3'
                        },
                        {
                            'ip_address': '10.0.0.4'
                        }
                    ],
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

        # Call update port
        port.update(args=new_config)

    def test_create_external_port(self, mock_connection):
        # Prepare relationship data which is connected to external port
        # resource
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
        ]

        port_rels = self.get_mock_relationship_ctx_for_node(rel_specs)

        # Update external port, will be part of create operation when use
        # external resource is set to True
        properties = dict()
        # Enable external resource
        properties['use_external_resource'] = True

        # Add node properties config to this dict
        properties.update(self.node_properties)
        # Reset resource config since we are going to use external resource
        # and do not care about the resource config data
        properties['resource_config'] = {}
        # Set resource id so that we can lookup the external resource
        properties['resource_config']['id'] = \
            'a95b5509-c122-4c2f-823e-884bb559afe1'

        # Set allowed address resource pairs
        properties['resource_config']['allowed_address_pairs'] = [
            {
                'ip_address': '10.0.0.5'
            },

            {
                'ip_address': '10.0.0.6'
            }
        ]

        self._prepare_context_for_operation(
            test_name='PortTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.create',
            test_properties=properties,
            test_relationships=port_rels)

        port_instance = openstack.network.v2.port.Port(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe1',
            'name': 'test_port',
            'admin_state_up': True,
            'binding_host_id': '3',
            'binding_profile': {'4': 4},
            'binding_vif_details': {'5': 5},
            'binding_vif_type': '6',
            'binding_vnic_type': '7',
            'created_at': '2016-03-09T12:14:57.233772',
            'data_plane_status': '32',
            'description': 'port_description',
            'device_id': '9',
            'device_owner': '10',
            'dns_assignment': [{'11': 11}],
            'dns_domain': 'a11',
            'dns_name': '12',
            'extra_dhcp_opts': [{'13': 13}],
            'fixed_ips': [{'10.0.0.1': '10.0.0.2'}],
            'allowed_address_pairs': [
                {
                    'ip_address': '10.0.0.3'
                },
                {
                    'ip_address': '10.0.0.4'
                }
            ],
            'mac_address': '00-14-22-01-23-45',
            'network_id': 'a95b5509-c122-4c2f-823e-884bb559afe4',
            'port_security_enabled': True,
            'qos_policy_id': '21',
            'revision_number': 22,
            'security_groups': ['23'],
            'status': '25',
            'tenant_id': '26',
            'updated_at': '2016-07-09T12:14:57.233772',
        })

        updated_port_instance = openstack.network.v2.port.Port(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe1',
            'name': 'test_port',
            'admin_state_up': True,
            'binding_host_id': '3',
            'binding_profile': {'4': 4},
            'binding_vif_details': {'5': 5},
            'binding_vif_type': '6',
            'binding_vnic_type': '7',
            'created_at': '2016-03-09T12:14:57.233772',
            'data_plane_status': '32',
            'description': 'port_description',
            'device_id': '9',
            'device_owner': '10',
            'dns_assignment': [{'11': 11}],
            'dns_domain': 'a11',
            'dns_name': '12',
            'extra_dhcp_opts': [{'13': 13}],
            'fixed_ips': [{'10.0.0.1': '10.0.0.2'}],
            'allowed_address_pairs': [
                {
                    'ip_address': '10.0.0.3'
                },
                {
                    'ip_address': '10.0.0.4'
                },
                {
                    'ip_address': '10.0.0.5'
                },
                {
                    'ip_address': '10.0.0.6'
                }
            ],
            'mac_address': '00-14-22-01-23-45',
            'network_id': 'a95b5509-c122-4c2f-823e-884bb559afe4',
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
            mock.MagicMock(return_value=port_instance)

        # Mock update port response
        mock_connection().network.update_port = \
            mock.MagicMock(return_value=updated_port_instance)

        # Call create port
        port.create()

        for attr in [RESOURCE_ID,
                     OPENSTACK_NAME_PROPERTY,
                     OPENSTACK_TYPE_PROPERTY,
                     'fixed_ips',
                     'mac_address',
                     'allowed_address_pairs']:
            self.assertIn(attr, self._ctx.instance.runtime_properties)

    def test_delete_external_port(self, mock_connection):
        # Prepare relationship data which is connected to external port
        # resource
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
        ]

        port_rels = self.get_mock_relationship_ctx_for_node(rel_specs)

        properties = dict()
        # Enable external resource
        properties['use_external_resource'] = True

        # Add node properties config to this dict
        properties.update(self.node_properties)
        # Reset resource config since we are going to use external resource
        # and do not care about the resource config data
        properties['resource_config'] = {}
        # Set resource id so that we can lookup the external resource
        properties['resource_config']['id'] = \
            'a95b5509-c122-4c2f-823e-884bb559afe1'

        # Set allowed address resource pairs
        properties['resource_config']['allowed_address_pairs'] = [
            {
                'ip_address': '10.0.0.5'
            },

            {
                'ip_address': '10.0.0.6'
            }
        ]

        self._prepare_context_for_operation(
            test_name='PortTestCase',
            ctx_operation_name='cloudify.interfaces.lifecycle.delete',
            test_properties=properties,
            test_relationships=port_rels,
            test_runtime_properties={
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe1'
            })

        port_instance = openstack.network.v2.port.Port(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe1',
            'name': 'test_port',
            'admin_state_up': True,
            'binding_host_id': '3',
            'binding_profile': {'4': 4},
            'binding_vif_details': {'5': 5},
            'binding_vif_type': '6',
            'binding_vnic_type': '7',
            'created_at': '2016-03-09T12:14:57.233772',
            'data_plane_status': '32',
            'description': 'port_description',
            'device_id': '9',
            'device_owner': '10',
            'dns_assignment': [{'11': 11}],
            'dns_domain': 'a11',
            'dns_name': '12',
            'extra_dhcp_opts': [{'13': 13}],
            'fixed_ips': [{'10.0.0.1': '10.0.0.2'}],
            'allowed_address_pairs': [
                {
                    'ip_address': '10.0.0.3'
                },
                {
                    'ip_address': '10.0.0.4'
                },
                {
                    'ip_address': '10.0.0.5'
                },
                {
                    'ip_address': '10.0.0.6'
                }
            ],
            'mac_address': '00-14-22-01-23-45',
            'network_id': 'a95b5509-c122-4c2f-823e-884bb559afe4',
            'port_security_enabled': True,
            'qos_policy_id': '21',
            'revision_number': 22,
            'security_groups': ['23'],
            'status': '25',
            'tenant_id': '26',
            'updated_at': '2016-07-09T12:14:57.233772',
        })

        updated_port_instance = openstack.network.v2.port.Port(**{
            'id': 'a95b5509-c122-4c2f-823e-884bb559afe1',
            'name': 'test_port',
            'admin_state_up': True,
            'binding_host_id': '3',
            'binding_profile': {'4': 4},
            'binding_vif_details': {'5': 5},
            'binding_vif_type': '6',
            'binding_vnic_type': '7',
            'created_at': '2016-03-09T12:14:57.233772',
            'data_plane_status': '32',
            'description': 'port_description',
            'device_id': '9',
            'device_owner': '10',
            'dns_assignment': [{'11': 11}],
            'dns_domain': 'a11',
            'dns_name': '12',
            'extra_dhcp_opts': [{'13': 13}],
            'fixed_ips': [{'10.0.0.1': '10.0.0.2'}],
            'allowed_address_pairs': [
                {
                    'ip_address': '10.0.0.3'
                },
                {
                    'ip_address': '10.0.0.4'
                }
            ],
            'mac_address': '00-14-22-01-23-45',
            'network_id': 'a95b5509-c122-4c2f-823e-884bb559afe4',
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
            mock.MagicMock(return_value=port_instance)

        # Mock update port response
        mock_connection().network.update_port = \
            mock.MagicMock(return_value=updated_port_instance)

        # Call delete port
        port.delete()

        for attr in [RESOURCE_ID,
                     OPENSTACK_NAME_PROPERTY,
                     OPENSTACK_TYPE_PROPERTY,
                     'fixed_ips',
                     'mac_address',
                     'allowed_address_pairs']:
            self.assertNotIn(attr, self._ctx.instance.runtime_properties)

    def test_list_ports(self, mock_connection):
        # Prepare the context for list ports operation
        self._prepare_context_for_operation(
            test_name='PortTestCase',
            ctx_operation_name='cloudify.interfaces.operations.list')

        ports = [
            openstack.network.v2.port.Port(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe1',
                'name': 'test_port_1',
                'admin_state_up': True,
                'binding_host_id': '3',
                'binding_profile': {'4': 4},
                'binding_vif_details': {'5': 5},
                'binding_vif_type': '6',
                'binding_vnic_type': '7',
                'created_at': '2016-03-09T12:14:57.233772',
                'data_plane_status': '32',
                'description': 'port_description_2',
                'device_id': '9',
                'device_owner': '10',
                'dns_assignment': [{'11': 11}],
                'dns_domain': 'a11',
                'dns_name': '12',
                'extra_dhcp_opts': [{'13': 13}],
                'fixed_ips': [{'10.0.0.1': '10.0.0.2'}],
                'allowed_address_pairs':
                    [
                        {
                            'ip_address': '10.0.0.3'
                        },
                        {
                            'ip_address': '10.0.0.4'
                        }
                    ],
                'mac_address': '00-14-22-01-23-45',
                'network_id': '18',
                'port_security_enabled': True,
                'qos_policy_id': '21',
                'revision_number': 22,
                'security_groups': ['23'],
                'status': '25',
                'tenant_id': '26',
                'updated_at': '2016-07-09T12:14:57.233772',
            }),
            openstack.network.v2.port.Port(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe2',
                'name': 'test_port_1',
                'admin_state_up': True,
                'binding_host_id': '3',
                'binding_profile': {'4': 4},
                'binding_vif_details': {'5': 5},
                'binding_vif_type': '6',
                'binding_vnic_type': '7',
                'created_at': '2016-03-09T12:14:57.233772',
                'data_plane_status': '32',
                'description': 'port_description_2',
                'device_id': '9',
                'device_owner': '10',
                'dns_assignment': [{'11': 11}],
                'dns_domain': 'a11',
                'dns_name': '12',
                'extra_dhcp_opts': [{'13': 13}],
                'fixed_ips': [{'10.0.0.3': '10.0.0.4'}],
                'allowed_address_pairs':
                    [
                        {
                            'ip_address': '10.0.0.3'
                        },
                        {
                            'ip_address': '10.0.0.4'
                        }
                    ],
                'mac_address': '00-41-23-23-23-24',
                'network_id': '18',
                'port_security_enabled': True,
                'qos_policy_id': '21',
                'revision_number': 22,
                'security_groups': ['23'],
                'status': '25',
                'tenant_id': '26',
                'updated_at': '2016-07-09T12:14:57.233772',
            }),
        ]

        # Mock list port response
        mock_connection().network.ports = mock.MagicMock(return_value=ports)

        # Mock find project response
        mock_connection().identity.find_project = \
            mock.MagicMock(return_value=self.project_resource)

        # Call list ports
        port.list_ports()

        # Check if the ports list saved as runtime properties
        self.assertIn(
            'port_list',
            self._ctx.instance.runtime_properties)

        # Check the size of ports list
        self.assertEqual(
            len(self._ctx.instance.runtime_properties['port_list']), 2)

    @mock.patch('openstack_sdk.common.OpenstackResource.get_quota_sets')
    def test_creation_validation(self, mock_quota_sets, mock_connection):
        # Prepare the context for creation validation operation
        self._prepare_context_for_operation(
            test_name='PortTestCase',
            ctx_operation_name='cloudify.interfaces.validation.creation')

        ports = [
            openstack.network.v2.port.Port(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe1',
                'name': 'test_port_1',
                'admin_state_up': True,
                'binding_host_id': '3',
                'binding_profile': {'4': 4},
                'binding_vif_details': {'5': 5},
                'binding_vif_type': '6',
                'binding_vnic_type': '7',
                'created_at': '2016-03-09T12:14:57.233772',
                'data_plane_status': '32',
                'description': 'port_description_2',
                'device_id': '9',
                'device_owner': '10',
                'dns_assignment': [{'11': 11}],
                'dns_domain': 'a11',
                'dns_name': '12',
                'extra_dhcp_opts': [{'13': 13}],
                'fixed_ips': [{'10.0.0.1': '10.0.0.2'}],
                'allowed_address_pairs':
                    [
                        {
                            'ip_address': '10.0.0.3'
                        },
                        {
                            'ip_address': '10.0.0.4'
                        }
                    ],
                'mac_address': '00-14-22-01-23-45',
                'network_id': '18',
                'port_security_enabled': True,
                'qos_policy_id': '21',
                'revision_number': 22,
                'security_groups': ['23'],
                'status': '25',
                'tenant_id': '26',
                'updated_at': '2016-07-09T12:14:57.233772',
            }),
            openstack.network.v2.port.Port(**{
                'id': 'a95b5509-c122-4c2f-823e-884bb559afe2',
                'name': 'test_port_1',
                'admin_state_up': True,
                'binding_host_id': '3',
                'binding_profile': {'4': 4},
                'binding_vif_details': {'5': 5},
                'binding_vif_type': '6',
                'binding_vnic_type': '7',
                'created_at': '2016-03-09T12:14:57.233772',
                'data_plane_status': '32',
                'description': 'port_description_2',
                'device_id': '9',
                'device_owner': '10',
                'dns_assignment': [{'11': 11}],
                'dns_domain': 'a11',
                'dns_name': '12',
                'extra_dhcp_opts': [{'13': 13}],
                'fixed_ips': [{'10.0.0.3': '10.0.0.4'}],
                'allowed_address_pairs':
                    [
                        {
                            'ip_address': '10.0.0.3'
                        },
                        {
                            'ip_address': '10.0.0.4'
                        }
                    ],
                'mac_address': '00-41-23-23-23-24',
                'network_id': '18',
                'port_security_enabled': True,
                'qos_policy_id': '21',
                'revision_number': 22,
                'security_groups': ['23'],
                'status': '25',
                'tenant_id': '26',
                'updated_at': '2016-07-09T12:14:57.233772',
            }),
        ]

        # Mock list port response
        mock_connection().network.ports = mock.MagicMock(return_value=ports)

        # Mock the quota size response
        mock_quota_sets.return_value = 20

        # Call creation validation
        port.creation_validation()
