########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import random
import logging
import os
import time
import copy
from contextlib import contextmanager

from cinderclient.v1 import client as cinderclient
import novaclient.v1_1.client as nvclient
import neutronclient.v2_0.client as neclient
from retrying import retry

from cosmo_tester.framework.handlers import (
    BaseHandler,
    BaseCloudifyInputsConfigReader)
from cosmo_tester.framework.util import get_actual_keypath


logging.getLogger('neutronclient.client').setLevel(logging.INFO)
logging.getLogger('novaclient.client').setLevel(logging.INFO)


class OpenstackCleanupContext(BaseHandler.CleanupContext):

    def __init__(self, context_name, env):
        super(OpenstackCleanupContext, self).__init__(context_name, env)
        self.before_run = self.env.handler.openstack_infra_state()

    def cleanup(self):
        super(OpenstackCleanupContext, self).cleanup()
        resources_to_teardown = self.get_resources_to_teardown()
        if self.skip_cleanup:
            self.logger.warn('[{0}] SKIPPING cleanup: of the resources: {1}'
                             .format(self.context_name, resources_to_teardown))
            return
        self.logger.info('[{0}] Performing cleanup: will try removing these '
                         'resources: {1}'
                         .format(self.context_name, resources_to_teardown))

        leftovers = self.env.handler.remove_openstack_resources(
            resources_to_teardown)
        self.logger.info('[{0}] Leftover resources after cleanup: {1}'
                         .format(self.context_name, leftovers))

    def get_resources_to_teardown(self):
        current_state = self.env.handler.openstack_infra_state()
        return self.env.handler.openstack_infra_state_delta(
            before=self.before_run, after=current_state)


class CloudifyOpenstackInputsConfigReader(BaseCloudifyInputsConfigReader):

    def __init__(self, cloudify_config, manager_blueprint_path, **kwargs):
        super(CloudifyOpenstackInputsConfigReader, self).__init__(
            cloudify_config, manager_blueprint_path=manager_blueprint_path,
            **kwargs)

    @property
    def region(self):
        return self.config['region']

    @property
    def management_server_name(self):
        return self.config['manager_server_name']

    @property
    def agent_key_path(self):
        return self.config['agent_private_key_path']

    @property
    def management_user_name(self):
        return self.config['manager_server_user']

    @property
    def management_key_path(self):
        return self.config['manager_private_key_path']

    @property
    def agent_keypair_name(self):
        return self.config['agent_public_key_name']

    @property
    def management_keypair_name(self):
        return self.config['manager_public_key_name']

    @property
    def external_network_name(self):
        return self.config['external_network_name']

    @property
    def keystone_username(self):
        return self.config['keystone_username']

    @property
    def keystone_password(self):
        return self.config['keystone_password']

    @property
    def keystone_tenant_name(self):
        return self.config['keystone_tenant_name']

    @property
    def keystone_url(self):
        return self.config['keystone_url']

    @property
    def neutron_url(self):
        return self.config.get('neutron_url', None)

    @property
    def management_network_name(self):
        return self.config['management_network_name']

    @property
    def management_subnet_name(self):
        return self.config['management_subnet_name']

    @property
    def management_router_name(self):
        return self.config['management_router']

    @property
    def agents_security_group(self):
        return self.config['agents_security_group_name']

    @property
    def management_security_group(self):
        return self.config['manager_security_group_name']


class OpenstackHandler(BaseHandler):

    CleanupContext = OpenstackCleanupContext
    CloudifyConfigReader = CloudifyOpenstackInputsConfigReader

    def before_bootstrap(self):
        super(OpenstackHandler, self).before_bootstrap()
        with self.update_cloudify_config() as patch:
            suffix = '-%06x' % random.randrange(16 ** 6)
            server_name_prop_path = \
                'compute.management_server.instance.name' if \
                self.env.is_provider_bootstrap else 'manager_server_name'
            patch.append_value(server_name_prop_path, suffix)

    def after_bootstrap(self, provider_context):
        super(OpenstackHandler, self).after_bootstrap(provider_context)
        resources = provider_context['resources']
        agent_keypair = resources['agents_keypair']
        management_keypair = resources['management_keypair']
        self.remove_agent_keypair = agent_keypair['external_resource'] is False
        self.remove_management_keypair = \
            management_keypair['external_resource'] is False

    def after_teardown(self):
        super(OpenstackHandler, self).after_teardown()
        if self.remove_agent_keypair:
            agent_key_path = get_actual_keypath(self.env,
                                                self.env.agent_key_path,
                                                raise_on_missing=False)
            if agent_key_path:
                os.remove(agent_key_path)
        if self.remove_management_keypair:
            management_key_path = get_actual_keypath(
                self.env,
                self.env.management_key_path,
                raise_on_missing=False)
            if management_key_path:
                os.remove(management_key_path)

    def openstack_clients(self):
        creds = self._client_creds()
        return (nvclient.Client(**creds),
                neclient.Client(username=creds['username'],
                                password=creds['api_key'],
                                tenant_name=creds['project_id'],
                                region_name=creds['region_name'],
                                auth_url=creds['auth_url']),
                cinderclient.Client(**creds))

    @retry(stop_max_attempt_number=5, wait_fixed=20000)
    def openstack_infra_state(self):
        """
        @retry decorator is used because this error sometimes occur:
        ConnectionFailed: Connection to neutron failed: Maximum
        attempts reached
        """
        nova, neutron, cinder = self.openstack_clients()
        prefix = self.env.resources_prefix
        return {
            'networks': dict(self._networks(neutron, prefix)),
            'subnets': dict(self._subnets(neutron, prefix)),
            'routers': dict(self._routers(neutron, prefix)),
            'security_groups': dict(self._security_groups(neutron, prefix)),
            'servers': dict(self._servers(nova, prefix)),
            'key_pairs': dict(self._key_pairs(nova, prefix)),
            'floatingips': dict(self._floatingips(neutron, prefix)),
            'ports': dict(self._ports(neutron, prefix)),
            'volumes': dict(self._volumes(cinder, prefix))
        }

    def openstack_infra_state_delta(self, before, after):
        after = copy.deepcopy(after)
        return {
            prop: self._remove_keys(after[prop], before[prop].keys())
            for prop in before.keys()
        }

    def remove_openstack_resources(self, resources_to_remove):
        # basically sort of a workaround, but if we get the order wrong
        # the first time, there is a chance things would better next time
        # 3'rd time can't really hurt, can it?
        # 3 is a charm
        for _ in range(3):
            resources_to_remove = self._remove_openstack_resources_impl(
                resources_to_remove)
            if all([len(g) == 0 for g in resources_to_remove.values()]):
                break
            # give openstack some time to update its data structures
            time.sleep(3)
        return resources_to_remove

    def _remove_openstack_resources_impl(self, resources_to_remove):
        nova, neutron, cinder = self.openstack_clients()

        servers = nova.servers.list()
        ports = neutron.list_ports()['ports']
        routers = neutron.list_routers()['routers']
        subnets = neutron.list_subnets()['subnets']
        networks = neutron.list_networks()['networks']
        keypairs = nova.keypairs.list()
        floatingips = neutron.list_floatingips()['floatingips']
        security_groups = neutron.list_security_groups()['security_groups']
        volumes = cinder.volumes.list()

        failed = {
            'servers': {},
            'routers': {},
            'ports': {},
            'subnets': {},
            'networks': {},
            'key_pairs': {},
            'floatingips': {},
            'security_groups': {},
            'volumes': {}
        }

        for server in servers:
            if server.id in resources_to_remove['servers']:
                with self._handled_exception(server.id, failed, 'servers'):
                    nova.servers.delete(server)
        for router in routers:
            if router['id'] in resources_to_remove['routers']:
                with self._handled_exception(router['id'], failed, 'routers'):
                    for p in neutron.list_ports(
                            device_id=router['id'])['ports']:
                        neutron.remove_interface_router(router['id'], {
                            'port_id': p['id']
                        })
                    neutron.delete_router(router['id'])
        for port in ports:
            if port['id'] in resources_to_remove['ports']:
                with self._handled_exception(port['id'], failed, 'ports'):
                    neutron.delete_port(port['id'])
        for subnet in subnets:
            if subnet['id'] in resources_to_remove['subnets']:
                with self._handled_exception(subnet['id'], failed, 'subnets'):
                    neutron.delete_subnet(subnet['id'])
        for network in networks:
            if network['name'] == self.env.external_network_name:
                continue
            if network['id'] in resources_to_remove['networks']:
                with self._handled_exception(network['id'], failed,
                                             'networks'):
                    neutron.delete_network(network['id'])
        for key_pair in keypairs:
            if key_pair.id in resources_to_remove['key_pairs']:
                with self._handled_exception(key_pair.id, failed, 'key_pairs'):
                    nova.keypairs.delete(key_pair)
        for floatingip in floatingips:
            if floatingip['id'] in resources_to_remove['floatingips']:
                with self._handled_exception(floatingip['id'], failed,
                                             'floatingips'):
                    neutron.delete_floatingip(floatingip['id'])
        for security_group in security_groups:
            if security_group['name'] == 'default':
                continue
            if security_group['id'] in resources_to_remove['security_groups']:
                with self._handled_exception(security_group['id'],
                                             failed, 'security_groups'):
                    neutron.delete_security_group(security_group['id'])
        for volume in volumes:
            if volume.id in resources_to_remove['volumes']:
                with self._handled_exception(volume.id, failed, 'volumes'):
                    cinder.volumes.delete(volume)

        return failed

    def _client_creds(self):
        return {
            'username': self.env.keystone_username,
            'api_key': self.env.keystone_password,
            'auth_url': self.env.keystone_url,
            'project_id': self.env.keystone_tenant_name,
            'region_name': self.env.region
        }

    def _networks(self, neutron, prefix):
        return [(n['id'], n['name'])
                for n in neutron.list_networks()['networks']
                if self._check_prefix(n['name'], prefix)]

    def _subnets(self, neutron, prefix):
        return [(n['id'], n['name'])
                for n in neutron.list_subnets()['subnets']
                if self._check_prefix(n['name'], prefix)]

    def _routers(self, neutron, prefix):
        return [(n['id'], n['name'])
                for n in neutron.list_routers()['routers']
                if self._check_prefix(n['name'], prefix)]

    def _security_groups(self, neutron, prefix):
        return [(n['id'], n['name'])
                for n in neutron.list_security_groups()['security_groups']
                if self._check_prefix(n['name'], prefix)]

    def _servers(self, nova, prefix):
        return [(s.id, s.human_id)
                for s in nova.servers.list()
                if self._check_prefix(s.human_id, prefix)]

    def _key_pairs(self, nova, prefix):
        return [(kp.id, kp.name)
                for kp in nova.keypairs.list()
                if self._check_prefix(kp.name, prefix)]

    def _floatingips(self, neutron, prefix):
        return [(ip['id'], ip['floating_ip_address'])
                for ip in neutron.list_floatingips()['floatingips']]

    def _ports(self, neutron, prefix):
        return [(p['id'], p['name'])
                for p in neutron.list_ports()['ports']
                if self._check_prefix(p['name'], prefix)]

    def _volumes(self, cinder, prefix):
        return [(v.id, v.display_name) for v in cinder.volumes.list()
                if self._check_prefix(v.display_name, prefix)]

    def _check_prefix(self, name, prefix):
        return name.startswith(prefix)

    def _remove_keys(self, dct, keys):
        for key in keys:
            if key in dct:
                del dct[key]
        return dct

    @contextmanager
    def _handled_exception(self, resource_id, failed, resource_group):
        try:
            yield
        except BaseException, ex:
            failed[resource_group][resource_id] = ex

handler = OpenstackHandler
