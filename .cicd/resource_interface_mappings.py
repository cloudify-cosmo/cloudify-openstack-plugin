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

from openstack import connect


class InterfaceBase(object):

    def __init__(self, resource_id, client_config):
        self.id = resource_id
        self.client_config = client_config

    @property
    def client(self):
        openstack_connecton = connect(**self.client_config)
        return getattr(openstack_connecton, self.client_name)

    def get(self):
        get_method = getattr(self.client, self.get_method_name)
        return get_method(self.id)

    def delete(self):
        delete_method = getattr(self.client, self.delete_method_name)
        return delete_method(self.id)


class Router(InterfaceBase):

    type_name = 'cloudify.nodes.openstack.Router'
    client_name = 'network'
    get_method_name = 'get_router'
    delete_method_name = 'delete_router'


class Network(InterfaceBase):

    type_name = 'cloudify.nodes.openstack.Network'
    client_name = 'network'
    get_method_name = 'get_network'
    delete_method_name = 'delete_network'


class Subnet(InterfaceBase):

    type_name = 'cloudify.nodes.openstack.Subnet'
    client_name = 'network'
    get_method_name = 'get_subnet'
    delete_method_name = 'delete_subnet'


class SecurityGroup(InterfaceBase):

    type_name = 'cloudify.nodes.openstack.SecurityGroup'
    client_name = 'network'
    get_method_name = 'get_security_group'
    delete_method_name = 'delete_security_group'


class Port(InterfaceBase):

    type_name = 'cloudify.nodes.openstack.Port'
    client_name = 'network'
    get_method_name = 'get_port'
    delete_method_name = 'delete_port'


class KeyPair(InterfaceBase):

    type_name = 'cloudify.nodes.openstack.KeyPair'
    client_name = 'compute'
    get_method_name = 'get_keypair'
    delete_method_name = 'delete_keypair'


class VolumeType(InterfaceBase):

    type_name = 'cloudify.nodes.openstack.VolumeType'
    client_name = 'block_storage'
    get_method_name = 'get_type'
    delete_method_name = 'delete_type'


class Server(InterfaceBase):

    type_name = 'cloudify.nodes.openstack.Server'
    client_name = 'compute'
    get_method_name = 'get_server'
    delete_method_name = 'delete_server'


class FloatingIP(InterfaceBase):

    type_name = 'cloudify.nodes.openstack.FloatingIP'
    client_name = 'compute'
    get_method_name = 'get_ip'
    delete_method_name = 'delete_ip'
