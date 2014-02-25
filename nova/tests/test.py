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

import argparse
import time
import unittest

from cloudify.mocks import MockCloudifyContext

import common as os_common

import nova.server as cfy_srv
import nova.monitor as cfy_srv_mon

tests_config = os_common.TestsConfig().get()

DELETE_WAIT_START = 1
DELETE_WAIT_FACTOR = 2
DELETE_WAIT_COUNT = 6


# WIP - start
# Maybe this chunk will not be needed as monitoring
# will be done differently, probably as a (celery) task
class MockReporter(object):
    state = {}

    def start(self, node_id, _host):
        self.__class__.state[node_id] = 'started'

    def stop(self, node_id, _host):
        self.__class__.state[node_id] = 'stopped'


def _mock_start_monitor(ctx):
    reporter = MockReporter(ctx)
    args = argparse.Namespace(monitor_interval=3,
                              region_name=None)
    monitor = cfy_srv_mon.OpenstackStatusMonitor(reporter, args)
    monitor.start()

cfy_srv.start_monitor = _mock_start_monitor
# WIP - end


class OpenstackNovaTest(os_common.TestCase):

    def test_server_create_and_delete(self):
        management_network = self.create_network('mng')

        nova_client = self.get_nova_client()
        name = self.name_prefix + 'srv_crt_del'
        ctx = MockCloudifyContext(
            node_id='__cloudify_id_' + name,
            properties={
                'server': {
                    'name': name,
                    'image_name': tests_config['image_name'],
                    'flavor': tests_config['flavor_id'],
                    'key_name': tests_config['key_name'],
                },
                'management_network_name': management_network['name']
            }
        )

        # Test: create
        self.assertThereIsNoServer(name=name)
        cfy_srv.create(ctx)
        self.assertThereIsOneServer(name=name)

        # WIP # # Test: start
        # WIP # cfy_srv.start(ctx)

        # WIP # # Test: stop
        # WIP # cfy_srv.stop(ctx)

        # Test: delete
        cfy_srv.delete(ctx)

        wait = DELETE_WAIT_START
        for attempt in range(1, DELETE_WAIT_COUNT + 1):
            servers = nova_client.servers.findall(name=name)
            if len(servers) == 0:
                break
            self.logger.debug(
                "Waiting for server {0} to disappear after deletion. "
                "Attempt #{1}, sleeping for {2} seconds".format(
                    name, attempt, wait))
            time.sleep(wait)
            wait *= DELETE_WAIT_FACTOR

        self.assertThereIsNoServer(name=name)

    @unittest.skip("Not implemented yet")
    def test_server_in_networks(self):
        pass

    def _create_networks(self):
        NETS = 3
        networks = []
        for i in range(0, NETS):
            network = self.create_network('net_' + str(i))
            self.create_subnet('subnet_' + str(i), '10.1.' + str(i) + '.0/24')
            networks.append(network)
        return networks

    def test_server_with_ports(self):
        name = self.name_prefix + 'srv_w_ports'

        management_network = self.create_network('mng')

        networks = self._create_networks()
        ports = [self.create_port('port_' + str(i), n)
                 for i, n in enumerate(networks)]

        related = {}
        for i, port in enumerate(ports):
            related['related_port_' + str(i)] = {'external_id': port['id']}

        ctx = MockCloudifyContext(
            node_id='__cloudify_id_' + name,
            properties={
                'server': {
                    'name': name,
                    'image_name': tests_config['image_name'],
                    'flavor': tests_config['flavor_id'],
                    'key_name': tests_config['key_name'],
                },
                'management_network_name': management_network['name']
            },
            related=related
        )
        self.assertThereIsNoServer(name=name)
        cfy_srv.create(ctx)
        self.assertThereIsOneServer(name=name)


if __name__ == '__main__':
    unittest.main()
    # _mock_start_monitor(object())
