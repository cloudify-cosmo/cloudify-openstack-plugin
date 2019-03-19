
# Monkey patch the "get_server_password" because the the current method for
# openstacksdk https://bit.ly/2zxA3At assume there is an instance variable
# called "_session" and it failed with error that "Proxy" class does not
# have such variable

from openstack.compute.v2 import _proxy as custom_proxy
from openstack.compute.v2 import server as _server


def get_server_password(self, server):
    """Get the administrator password

    :param server: Either the ID of a server or a
                   :class:`~openstack.compute.v2.server.Server` instance.

    :returns: encrypted password.
    """
    server = self._get_resource(_server.Server, server)
    return server.get_password(self)


custom_proxy.Proxy.get_server_password = get_server_password
