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

# Monkey patch are using in the following methods because of issues using
# the underlying SDDK (OpenstackSDK)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                    # get_server_password #                                #
#                                                                           #
# Monkey patch the "get_server_password" because the current method for     #
# openstacksdk https://bit.ly/2zxA3At assume there is an instance variable  #
# called "_session" and it failed with error that "Proxy" class does not    #
# have such variable                                                        #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#    add_security_group_to_server & remove_security_group_from_server       #
#                                                                           #
#                                                                           #
# The reason why we are using monkey patch is because getting the security  #
# group using "_get_resource" return object with missing values including   #
# "name" returned as None which cause error when trying to add/remove       #
# security group to/from server since name cannot be empty. The issue will  #
# be in the following snippet:                                              #
#                                                                           #
# server.add_security_group(self, security_group.name)                      #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


from openstack.compute.v2 import _proxy as custom_proxy
from openstack.compute.v2 import server as _server
from openstack.network.v2 import security_group as _sg


def get_server_password(self, server):
    """Get the administrator password

    :param server: Either the ID of a server or a
                   :class:`~openstack.compute.v2.server.Server` instance.

    :returns: encrypted password.
    """
    server = self._get_resource(_server.Server, server)
    return server.get_password(self)


def add_security_group_to_server(self, server, security_group):
    """Add a security group to a server

    :param server: Either the ID of a server or a
        :class:`~openstack.compute.v2.server.Server` instance.
    :param security_group: Either the ID, Name of a security group or a
        :class:`~openstack.network.v2.security_group.SecurityGroup`
        instance.

    :returns: None
    """
    server = self._get_resource(_server.Server, server)
    security_group = self._get_resource(_sg.SecurityGroup, security_group)
    server.add_security_group(self, security_group.id)


def remove_security_group_from_server(self, server, security_group):
    """Remove a security group from a server

    :param server: Either the ID of a server or a
        :class:`~openstack.compute.v2.server.Server` instance.
    :param security_group: Either the ID of a security group or a
        :class:`~openstack.network.v2.security_group.SecurityGroup`
        instance.

    :returns: None
    """
    server = self._get_resource(_server.Server, server)
    security_group = self._get_resource(_sg.SecurityGroup, security_group)
    server.remove_security_group(self, security_group.id)


custom_proxy.Proxy.add_security_group_to_server = \
    add_security_group_to_server

custom_proxy.Proxy.remove_security_group_from_server = \
    remove_security_group_from_server

custom_proxy.Proxy.get_server_password = get_server_password
