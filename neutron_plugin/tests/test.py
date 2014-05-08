#########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  * See the License for the specific language governing permissions and
#  * limitations under the License.

import unittest

import openstack_plugin_common as common
import neutron_plugin.floatingip as cfy_fip
import neutron_plugin.network as cfy_net
import neutron_plugin.port as cfy_port
import neutron_plugin.router as cfy_rtr
import neutron_plugin.security_group as cfy_sg

from cloudify.context import ContextCapabilities
from cloudify.mocks import MockCloudifyContext


class OpenstackNeutronTest(common.TestCase):

    def test_port(self):
        name = self.name_prefix + 'the_port'
        network = self.create_network('for_port')
        self.create_subnet('for_port', '10.11.12.0/24', network=network)
        sg = self.create_sg('for_port')

        ctx = MockCloudifyContext(
            node_id='__cloudify_id_' + name + '_port',
            properties={'port': {'name': name}},
            capabilities=ContextCapabilities({
                'net_node': {
                    'external_id': network['id']
                }
            })
        )

        cfy_port.create(ctx)
        self.assertThereIsOne('port', name=name)

        ctx_conn = MockCloudifyContext(
            runtime_properties=ctx.runtime_properties,
            related=MockCloudifyContext(
                runtime_properties={'external_id': sg['id']}
            )
        )
        cfy_port.connect_security_group(ctx_conn)
        port = self.assertThereIsOneAndGet('port', name=name)
        self.assertTrue(sg['id'] in port['security_groups'])

        cfy_port.delete(ctx)
        self.assertThereIsNo('port', name=name)

    def test_network(self):
        name = self.name_prefix + 'net'

        self.assertThereIsNo('network', name=name)

        ctx = MockCloudifyContext(
            node_id='__cloudify_id_' + name,
            properties={'network': {'name': name}},
        )

        cfy_net.create(ctx)

        net = self.assertThereIsOneAndGet('network', name=name)
        self.assertTrue(net['admin_state_up'])

        cfy_net.stop(ctx)
        net = self.assertThereIsOneAndGet('network', name=name)
        self.assertFalse(net['admin_state_up'])

        cfy_net.start(ctx)
        net = self.assertThereIsOneAndGet('network', name=name)
        self.assertTrue(net['admin_state_up'])

        cfy_net.delete(ctx)
        self.assertThereIsNo('network', name=name)

    def test_sg(self):
        neutron_client = self.get_neutron_client()

        # Test: group with all defaults + delete
        name = self.name_prefix + 'sg1'
        ctx = MockCloudifyContext(
            node_id='__cloudify_id_' + name,
            properties={
                'security_group': {
                    'name': name,
                    'description': 'SG-DESC',
                },
                'rules': []
            }
        )
        self.assertThereIsNo('security_group', name=name)
        cfy_sg.create(ctx)
        self.assertThereIsOne('security_group', name=name)

        # By default SG should have 2 egress rules and no ingress rules
        for direction, count in ('egress', 2), ('ingress', 0):
            rules = neutron_client.cosmo_list(
                'security_group_rule',
                security_group_id=ctx.runtime_properties['external_id'],
                direction=direction
            )
            ls = list(rules)
            # print(ls)
            self.assertEquals(len(ls), count)

        cfy_sg.delete(ctx)
        self.assertThereIsNo('security_group', name=name)

        # Test: Disabled egress
        name = self.name_prefix + 'sg2'
        ctx2 = MockCloudifyContext(
            node_id='__cloudify_id_' + name,
            properties={
                'security_group': {
                    'name': name,
                    'description': 'SG-DESC',
                },
                'rules': [],
                'disable_egress': True,
            }
        )
        self.assertThereIsNo('security_group', name=name)
        cfy_sg.create(ctx2)
        self.assertThereIsOne('security_group', name=name)
        rules = neutron_client.cosmo_list(
            'security_group_rule',
            security_group_id=ctx2.runtime_properties['external_id'],
        )
        ls = list(rules)
        self.assertEquals(len(ls), 0)
        cfy_sg.delete(ctx2)

        # Test: Exception when providing egress rule and "disable_egress"
        ctx2.properties['rules'] = [{
            'direction': 'egress',
            'port': 80,
        }]
        self.assertThereIsNo('security_group', name=name)
        self.assertRaises(RuntimeError, cfy_sg.create, ctx2)

        # Test: One egress rule
        del ctx2.properties['disable_egress']
        cfy_sg.create(ctx2)
        self.assertThereIsOne('security_group', name=name)
        rules = neutron_client.cosmo_list(
            'security_group_rule',
            security_group_id=ctx2.runtime_properties['external_id'],
            direction='egress',
        )
        ls = list(rules)
        self.assertEquals(len(ls), 1)

        # TODO: Test two related security groups

    def test_existing_floatingip(self):
        neutron_client = self.get_neutron_client()
        name = self.name_prefix + 'fip'

        floatingip = {
            'floating_network_id': neutron_client
            .cosmo_find_external_net()['id']
        }
        fip = neutron_client.create_floatingip({
            'floatingip': floatingip
        })['floatingip']
        ctx = MockCloudifyContext(
            node_id='__cloudify_id_' + name,
            properties={
                'floatingip': {
                    'ip': fip['floating_ip_address']
                }
            }
        )
        cfy_fip.create(ctx)
        # Make sure "allocated" id is the id of the floating ip we
        # allocated before the operation
        self.assertEqual(ctx.runtime_properties['external_id'], fip['id'])
        self.assertFalse(ctx.runtime_properties['enable_deletion'])
        cfy_fip.delete(ctx)
        ls = list(
            neutron_client.cosmo_list('floatingip',
                                      floating_ip_address=fip[
                                          'floating_ip_address']))
        self.assertEqual(len(ls), 1)

    def test_new_floatingip(self):
        neutron_client = self.get_neutron_client()
        name = self.name_prefix + 'fip'

        existing_fips = [fip['id'] for fip in neutron_client.cosmo_list(
            'floatingip')]

        ctx = MockCloudifyContext(
            node_id='__cloudify_id_' + name,
            properties={
                'floatingip': {
                    'floating_network_name':
                    neutron_client.cosmo_find_external_net()['name']
                }
            }
        )
        cfy_fip.create(ctx)
        self.assertNotIn(ctx.runtime_properties['external_id'], existing_fips)
        self.assertTrue(ctx.runtime_properties['enable_deletion'])
        cfy_fip.delete(ctx)
        ls = list(neutron_client.cosmo_list('floatingip'))
        self.assertEqual(len(ls), 0)

    def test_router_create_and_delete(self):
        name = self.name_prefix + 'rtr_prov_term'
        ctx = MockCloudifyContext(
            node_id='__cloudify_id_' + name,
            properties={
                'router': {
                    'name': name
                }
            }
        )

        self.assertThereIsNo('router', name=name)
        cfy_rtr.create(ctx)
        router = self.assertThereIsOneAndGet('router', name=name)
        # must not have gateway
        self.assertIsNone(router['external_gateway_info'])

        cfy_rtr.delete(ctx)
        self.assertThereIsNo('router', name=name)

    def _test_router_with_gateway(self, enable_snat):
        neutron_client = self.get_neutron_client()
        ext_net = neutron_client.cosmo_find_external_net()

        name = self.name_prefix + 'rtr_ext_gw_snat_'
        name += ['dis', 'ena'][enable_snat]
        ctx = MockCloudifyContext(
            node_id='__cloudify_id_' + name,
            properties={
                'router': {
                    'name': name,
                    'external_gateway_info': {
                        'network_name': ext_net['name'],
                        'enable_snat': enable_snat
                    }
                }
            }
        )

        cfy_rtr.create(ctx)
        rtr = self.assertThereIsOneAndGet('router', name=name)
        self.assertIsNotNone(rtr['external_gateway_info'])
        self.assertEquals(rtr['external_gateway_info']['network_id'],
                          ext_net['id'])
        self.assertEquals(rtr['external_gateway_info']['enable_snat'],
                          enable_snat)

    def test_router_with_gateway_snat_enabled(self):
        self._test_router_with_gateway(True)

    def test_router_with_gateway_snat_disabled(self):
        self._test_router_with_gateway(False)

    def test_router_connect_disconnect_subnet(self):
        # Router
        name = self.name_prefix + 'rtr_subn'
        ctx = MockCloudifyContext(
            node_id='__cloudify_id_' + name,
            properties={
                'router': {
                    'name': name
                }
            }
        )

        cfy_rtr.create(ctx)
        self.assertThereIsOneAndGet('router', name=name)

        network = self.create_network('for_port')
        subnet = self.create_subnet('for_port',
                                    '192.168.1.0/24',
                                    network=network)

        # Connect router and subnet
        ctx = MockCloudifyContext(
            node_id=ctx.node_id,
            runtime_properties=ctx.runtime_properties,
            properties=ctx.properties,
            related=MockCloudifyContext(
                runtime_properties={'external_id': subnet['id']}
            )
        )
        self.assertThereIsNo(
            'port',
            network_id=network['id'],
            device_id=ctx.runtime_properties['external_id']
        )
        cfy_rtr.connect_subnet(ctx)
        self.assertThereIsOne(
            'port',
            network_id=network['id'],
            device_id=ctx.runtime_properties['external_id']
        )

        cfy_rtr.disconnect_subnet(ctx)
        self.assertThereIsNo(
            'port',
            network_id=network['id'],
            device_id=ctx.runtime_properties['external_id']
        )


if __name__ == '__main__':
    unittest.main()
