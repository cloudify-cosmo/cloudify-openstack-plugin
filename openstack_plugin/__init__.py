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

from cloudify import ctx as ctx_src

from openstack.compute.v2 import server as _server
import openstack.compute.v2._proxy as proxy

# The reason why we are using monkey patch is because getting the security
# group using "_get_resource" return object with missing values including
# "name" returned as None which cause error whe  trying to add/remove server
# to/from security group since name cannot be empty
# security_group = self._get_resource(_sg.SecurityGroup, security_group)
# It so we had to monkey patch this to avoid the error


def add_security_group_to_server(self, server, security_group):
    """Add a security group to a server

    :param server: Either the ID of a server or a
        :class:`~openstack.compute.v2.server.Server` instance.
    :param security_group: Either the ID, Name of a security group or a
        :class:`~openstack.network.v2.security_group.SecurityGroup`
        instance.

    :returns: None
    """
    sg_name = ctx_src.target.instance.runtime_properties.get('name')
    server = self._get_resource(_server.Server, server)
    server.add_security_group(self, sg_name)


def remove_security_group_from_server(self, server, security_group):
    """Remove a security group from a server

    :param server: Either the ID of a server or a
        :class:`~openstack.compute.v2.server.Server` instance.
    :param security_group: Either the ID of a security group or a
        :class:`~openstack.network.v2.security_group.SecurityGroup`
        instance.

    :returns: None
    """
    sg_name = ctx_src.target.instance.runtime_properties.get('name')
    server = self._get_resource(_server.Server, server)
    server.remove_security_group(self, sg_name)


proxy.Proxy.add_security_group_to_server = \
    add_security_group_to_server

proxy.Proxy.remove_security_group_from_server = \
    remove_security_group_from_server
