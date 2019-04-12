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


# Based on this documentation:
# https://docs.openstack.org/openstacksdk/latest/user/proxies/network.html.

# Local imports
from openstack_sdk.common import (OpenstackResource, ResourceMixin)


class OpenstackNetwork(OpenstackResource):
    # SDK documentation link:
    # https://bit.ly/2D2S1xw.
    service_type = 'network'
    resource_type = 'network'

    def resource_plural(self, openstack_type):
        return openstack_type

    def list(self, query=None):
        query = query or {}
        if 'project_id' not in query:
            query['project_id'] = self.project_id
        return self.connection.network.networks(**query)

    def get(self):
        self.logger.debug(
            'Attempting to find this network: {0}'.format(self.resource_id))
        network = self.connection.network.get_network(self.resource_id)
        self.logger.debug(
            'Found network with this result: {0}'.format(network))
        return network

    def find_network(self, name_or_id=None):
        if not name_or_id:
            name_or_id = self.name if not\
                self.resource_id else self.resource_id
        self.logger.debug(
            'Attempting to find this network: {0}'.format(name_or_id))
        network = self.connection.network.find_network(name_or_id)
        self.logger.debug(
            'Found network with this result: {0}'.format(network))
        return network

    def create(self):
        self.logger.debug(
            'Attempting to create network with these args: {0}'.format(
                self.config))
        network = self.connection.network.create_network(**self.config)
        self.logger.debug(
            'Created network with this result: {0}'.format(network))
        return network

    def delete(self):
        network = self.get()
        self.logger.debug(
            'Attempting to delete this network: {0}'.format(network))
        result = self.connection.network.delete_network(network)
        self.logger.debug(
            'Deleted network with this result: {0}'.format(result))
        return result

    def update(self, new_config=None):
        network = self.get()
        self.logger.debug(
            'Attempting to update this network: {0} with args {1}'.format(
                network, new_config))
        result = self.connection.network.update_network(network, **new_config)
        self.logger.debug(
            'Updated network with this result: {0}'.format(result))
        return result


class OpenstackSubnet(OpenstackResource):
    # SDK documentation link:
    # https://bit.ly/2SMLuvY

    service_type = 'network'
    resource_type = 'subnet'

    def resource_plural(self, openstack_type):
        return openstack_type

    def list(self, query=None):
        query = query or {}
        if 'project_id' not in query:
            query['project_id'] = self.project_id
        return self.connection.network.subnets(**query)

    def get(self):
        self.logger.debug(
            'Attempting to find this subnet: {0}'.format(self.resource_id))
        subnet = self.connection.network.get_subnet(self.resource_id)
        self.logger.debug('Found subnet with this result: {0}'.format(subnet))
        return subnet

    def find_subnet(self, name_or_id=None):
        if not name_or_id:
            name_or_id = self.name if not\
                self.resource_id else self.resource_id
        self.logger.debug(
            'Attempting to find this subnet: {0}'.format(name_or_id))
        subnet = self.connection.network.find_subnet(
            name_or_id, project_id=self.project_id)
        self.logger.debug(
            'Found subnet with this result: {0}'.format(subnet))
        return subnet

    def create(self):
        self.logger.debug(
            'Attempting to create subnet with these args: {0}'.format(
                self.config))
        subnet = self.connection.network.create_subnet(**self.config)
        self.logger.debug(
            'Created subnet with this result: {0}'.format(subnet))
        return subnet

    def delete(self):
        subnet = self.get()
        self.logger.debug(
            'Attempting to delete this subnet: {0}'.format(subnet))
        result = self.connection.network.delete_subnet(subnet)
        self.logger.debug(
            'Deleted subnet with this result: {0}'.format(result))
        return result

    def update(self, new_config=None):
        subnet = self.get()
        self.logger.debug(
            'Attempting to update this subnet: {0} with args {1}'.format(
                subnet, new_config))
        result = self.connection.network.update_subnet(subnet, **new_config)
        self.logger.debug(
            'Updated subnet with this result: {0}'.format(result))
        return result


class OpenstackPort(OpenstackResource):
    # SDK documentation link:
    # https://bit.ly/2DlPnUj
    service_type = 'network'
    resource_type = 'port'

    def resource_plural(self, openstack_type):
        return openstack_type

    def list(self, query=None):
        query = query or {}
        if 'project_id' not in query:
            query['project_id'] = self.project_id
        return self.connection.network.ports(**query)

    def get(self):
        self.logger.debug(
            'Attempting to find this port: {0}'.format(self.resource_id))
        port = self.connection.network.get_port(self.resource_id)
        self.logger.debug(
            'Found port with this result: {0}'.format(port))
        return port

    def find_port(self, name_or_id=None):
        if not name_or_id:
            name_or_id = self.name if not\
                self.resource_id else self.resource_id
        self.logger.debug(
            'Attempting to find this port: {0}'.format(name_or_id))
        port = self.connection.network.find_port(
            name_or_id, project_id=self.project_id)
        self.logger.debug(
            'Found port with this result: {0}'.format(port))
        return port

    def create(self):
        self.logger.debug(
            'Attempting to create port with these args: {0}'.format(
                self.config))
        port = self.connection.network.create_port(**self.config)
        self.logger.debug(
            'Created port with this result: {0}'.format(port))
        return port

    def delete(self):
        port = self.get()
        self.logger.debug(
            'Attempting to delete this port: {0}'.format(port))
        result = self.connection.network.delete_port(port)
        self.logger.debug(
            'Deleted port with this result: {0}'.format(result))
        return result

    def update(self, new_config=None):
        port = self.get()
        self.logger.debug(
            'Attempting to update this port: {0} with args {1}'.format(
                port, new_config))
        result = self.connection.network.update_port(port, **new_config)
        self.logger.debug(
            'Updated port with this result: {0}'.format(result))
        return result


class OpenstackRouter(OpenstackResource):
    # SDK documentation link:
    # https://bit.ly/2QioQdg
    service_type = 'network'
    resource_type = 'router'

    def resource_plural(self, openstack_type):
        return openstack_type

    def list(self, query=None):
        query = query or {}
        if 'project_id' not in query:
            query['project_id'] = self.project_id
        return self.connection.network.routers(**query)

    def get(self):
        self.logger.debug(
            'Attempting to find this router: {0}'.format(self.resource_id))
        router = self.connection.network.get_router(self.resource_id)
        self.logger.debug('Found router with this result: {0}'.format(router))
        return router

    def find_router(self, name_or_id=None):
        if not name_or_id:
            name_or_id = self.name if not\
                self.resource_id else self.resource_id
        self.logger.debug(
            'Attempting to find this router: {0}'.format(name_or_id))
        router = self.connection.network.find_router(
            name_or_id, project_id=self.project_id)
        self.logger.debug(
            'Found router with this result: {0}'.format(router))
        return router

    def create(self):
        self.logger.debug(
            'Attempting to create router with these args: {0}'.format(
                self.config))
        router = self.connection.network.create_router(**self.config)
        self.logger.debug(
            'Created router with this result: {0}'.format(router))
        return router

    def delete(self):
        router = self.get()
        self.logger.debug(
            'Attempting to delete this router: {0}'.format(router))
        result = self.connection.network.delete_router(router)
        self.logger.debug(
            'Deleted router with this result: {0}'.format(result))
        return result

    def update(self, new_config=None):
        router = self.get()
        self.logger.debug(
            'Attempting to update this router: {0} with args {1}'.format(
                router, new_config))
        result = self.connection.network.update_router(router, **new_config)
        self.logger.debug(
            'Updated router with this result: {0}'.format(result))
        return result

    def add_interface(self, kwargs):
        router = self.get()
        self.logger.debug(
            'Attempting to add {0} interface this router: {1}'.format(
                kwargs, router))
        result = self.connection.network.add_interface_to_router(
            router, **kwargs)
        self.logger.debug(
            'Added this interface to router: {0}'.format(result))
        return result

    def remove_interface(self, kwargs):
        router = self.get()
        self.logger.debug(
            'Attempting to remove {0} interface this router: {1}'.format(
                kwargs, router))
        result = self.connection.network.remove_interface_from_router(
            router, **kwargs)
        self.logger.debug(
            'Removed this interface to router: {0}'.format(result))
        return result


class OpenstackFloatingIP(OpenstackResource):
    # SDK documentation link:
    # https://bit.ly/2JGHqcQ
    service_type = 'network'
    resource_type = 'floatingip'

    def resource_plural(self, openstack_type):
        return openstack_type

    def list(self, query=None):
        query = query or {}
        if 'project_id' not in query:
            query['project_id'] = self.project_id
        return self.connection.network.ips(**query)

    def get(self):
        self.logger.debug(
            'Attempting to find this floating ip: {0}'
            ''.format(self.resource_id))
        floating_ip = self.connection.network.get_ip(self.resource_id)
        self.logger.debug(
            'Found floating ip with this result: {0}'.format(floating_ip))
        return floating_ip

    def find_floatingip(self, name_or_id=None):
        if not name_or_id:
            name_or_id = self.name if not\
                self.resource_id else self.resource_id
        self.logger.debug(
            'Attempting to find this floating ip: {0}'.format(name_or_id))
        floating_ip = self.connection.network.find_ip(
            name_or_id, project_id=self.project_id)
        self.logger.debug(
            'Found floating ip with this result: {0}'.format(floating_ip))
        return floating_ip

    def create(self):
        self.logger.debug(
            'Attempting to create floating ip with these args: {0}'.format(
                self.config))
        floating_ip = self.connection.network.create_ip(**self.config)
        self.logger.debug(
            'Created floating ip with this result: {0}'.format(floating_ip))
        return floating_ip

    def delete(self):
        floating_ip = self.get()
        self.logger.debug(
            'Attempting to delete this floating ip: {0}'.format(floating_ip))
        self.connection.network.delete_ip(floating_ip)

    def update(self, new_config=None):
        floating_ip = self.get()
        self.logger.debug(
            'Attempting to update this floating ip: {0} with args {1}'.format(
                floating_ip, new_config))
        result = self.connection.network.update_ip(floating_ip, **new_config)
        self.logger.debug(
            'Updated floating ip with this result: {0}'.format(result))
        return result


class OpenstackSecurityGroup(OpenstackResource):
    # SDK documentation link:
    # https://bit.ly/2PCsWA0
    service_type = 'network'
    resource_type = 'security_group'

    def resource_plural(self, openstack_type):
        return openstack_type

    def list(self, query=None):
        query = query or {}
        if 'project_id' not in query:
            query['project_id'] = self.project_id
        return self.connection.network.security_groups(**query)

    def get(self):
        self.logger.debug(
            'Attempting to find this security group: {0}'
            ''.format(self.resource_id))
        security_group = self.connection.network.get_security_group(
            self.resource_id)
        self.logger.debug(
            'Found security group with this result: {0}'.format(
                security_group))
        return security_group

    def find_security_group(self, name_or_id=None):
        if not name_or_id:
            name_or_id = self.name if not\
                self.resource_id else self.resource_id
        self.logger.debug(
            'Attempting to find this security group: {0}'.format(name_or_id))
        security_group = self.connection.network.find_security_group(
            name_or_id, project_id=self.project_id)
        self.logger.debug(
            'Found security group with this result: {0}'.format(
                security_group))
        return security_group

    def create(self):
        self.logger.debug(
            'Attempting to create security group with these args: {0}'.format(
                self.config))
        security_group = self.connection.network.create_security_group(
            **self.config)
        self.logger.debug(
            'Created security group with this result: {0}'.format(
                security_group))
        return security_group

    def delete(self):
        security_group = self.get()
        self.logger.debug(
            'Attempting to delete this security_group: {0}'.format(
                security_group))
        result = self.connection.network.delete_security_group(security_group)
        self.logger.debug(
            'Deleted security group with this result: {0}'.format(result))
        return result

    def update(self, new_config=None):
        security_group = self.get()
        self.logger.debug('Attempting to update this '
                          'security group: {0} with args {1}'.format(
                              security_group, new_config))
        result = self.connection.network.update_security_group(
            security_group, **new_config)
        self.logger.debug(
            'Updated security group with this result: {0}'.format(result))
        return result


class OpenstackSecurityGroupRule(OpenstackResource):
    # SDK documentation link:
    # https://bit.ly/2PCsWA0
    service_type = 'network'
    resource_type = 'security_group_rule'

    def resource_plural(self, openstack_type):
        return openstack_type

    def list(self, query=None):
        query = query or {}
        if 'project_id' not in query:
            query['project_id'] = self.project_id
        return self.connection.network.security_group_rules(**query)

    def get(self):
        self.logger.debug(
            'Attempting to find this security group rule: {0}'
            ''.format(self.resource_id))
        security_group_rule = self.connection.network.get_security_group_rule(
            self.resource_id)
        self.logger.debug(
            'Found security group with this result: {0}'.format(
                security_group_rule))
        return security_group_rule

    def find_security_group_rule(self, name_or_id=None):
        if not name_or_id:
            name_or_id = self.name if not\
                self.resource_id else self.resource_id
        self.logger.debug(
            'Attempting to find '
            'this security group rule: {0}'.format(name_or_id))
        security_group_rule = \
            self.connection.network.find_security_group_rule(
                name_or_id, project_id=self.project_id)
        self.logger.debug(
            'Found security group with this result: {0}'.format(
                security_group_rule))
        return security_group_rule

    def create(self):
        self.logger.debug('Attempting to create security group rule '
                          'with these args: {0}'.format(self.config))
        security_group_rule = \
            self.connection.network.create_security_group_rule(**self.config)
        self.logger.debug(
            'Created security group rule with this result: {0}'.format(
                security_group_rule))
        return security_group_rule

    def delete(self):
        security_group_rule = self.get()
        self.logger.debug(
            'Attempting to delete this security group rule: {0}'.format(
                security_group_rule))
        result = self.connection.network.delete_security_group_rule(
            security_group_rule)
        self.logger.debug(
            'Deleted security group with this result: {0}'.format(result))
        return result


class OpenstackRBACPolicy(ResourceMixin, OpenstackResource):
    # SDK documentation link:
    # https://bit.ly/2DvKSnI
    service_type = 'network'
    resource_type = 'rbac_policy'

    def resource_plural(self, openstack_type):
        return 'rbac_policies'

    def list(self, query=None, all_projects=False):
        return self.list_resources(query, all_projects)

    def get(self):
        self.logger.debug(
            'Attempting to find this rbac policy: {0}'
            ''.format(self.resource_id))
        rbac_policy = self.connection.network.get_rbac_policy(self.resource_id)
        self.logger.debug(
            'Found rbac policy with this result: {0}'.format(rbac_policy))
        return rbac_policy

    def find_rbac_policy(self, name_or_id=None):
        if not name_or_id:
            name_or_id = self.name if not\
                self.resource_id else self.resource_id
        self.logger.debug(
            'Attempting to find this rbac policy: {0}'.format(name_or_id))
        rbac_policy = self.connection.network.find_rbac_policy(
            name_or_id, project_id=self.project_id)
        self.logger.debug(
            'Found rbac policy with this result: {0}'.format(rbac_policy))
        return rbac_policy

    def create(self):
        self.logger.debug('Attempting to create rbac policy '
                          'with these args: {0}'.format(self.config))
        rbac_policy = \
            self.connection.network.create_rbac_policy(**self.config)
        self.logger.debug(
            'Created rbac policy with this result: {0}'.format(rbac_policy))
        return rbac_policy

    def delete(self):
        rbac_policy = self.get()
        self.logger.debug(
            'Attempting to delete this rbac policy: {0}'.format(
                rbac_policy))
        result = self.connection.network.delete_rbac_policy(rbac_policy)
        self.logger.debug(
            'Deleted rbac policy with this result: {0}'.format(result))
        return result

    def update(self, new_config=None):
        rbac_policy = self.get()
        self.logger.debug(
            'Attempting to update this rbac policy: {0} with args {1}'
            ''.format(rbac_policy, new_config))
        result = self.connection.network.update_rbac_policy(
            rbac_policy, **new_config)
        self.logger.debug(
            'Updated rbac policy with this result: {0}'.format(result))
        return result
