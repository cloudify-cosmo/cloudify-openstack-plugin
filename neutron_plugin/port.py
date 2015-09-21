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

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

import neutronclient.common.exceptions as neutron_exceptions

from openstack_plugin_common import (
    transform_resource_name,
    with_neutron_client,
    get_resource_id,
    get_openstack_id_of_single_connected_node_by_openstack_type,
    delete_resource_and_runtime_properties,
    delete_runtime_properties,
    use_external_resource,
    is_external_relationship,
    validate_resource,
    OPENSTACK_ID_PROPERTY,
    OPENSTACK_TYPE_PROPERTY,
    OPENSTACK_NAME_PROPERTY,
    COMMON_RUNTIME_PROPERTIES_KEYS
)

from neutron_plugin.network import NETWORK_OPENSTACK_TYPE
from neutron_plugin.subnet import SUBNET_OPENSTACK_TYPE

PORT_OPENSTACK_TYPE = 'port'

# Runtime properties
FIXED_IP_ADDRESS_PROPERTY = 'fixed_ip_address'  # the fixed ip address
RUNTIME_PROPERTIES_KEYS = \
    COMMON_RUNTIME_PROPERTIES_KEYS + [FIXED_IP_ADDRESS_PROPERTY]

_NO_SG_PORT_CONNECTION_RETRY_INTERVAL = 3


@operation
@with_neutron_client
def create(neutron_client, **kwargs):

    ext_port = use_external_resource(ctx, neutron_client, PORT_OPENSTACK_TYPE)
    if ext_port:
        try:
            net_id = \
                get_openstack_id_of_single_connected_node_by_openstack_type(
                    ctx, NETWORK_OPENSTACK_TYPE, True)

            if net_id:
                port_id = ctx.instance.runtime_properties[
                    OPENSTACK_ID_PROPERTY]

                if neutron_client.show_port(
                        port_id)['port']['network_id'] != net_id:
                    raise NonRecoverableError(
                        'Expected external resources port {0} and network {1} '
                        'to be connected'.format(port_id, net_id))

            ctx.instance.runtime_properties[FIXED_IP_ADDRESS_PROPERTY] = \
                _get_fixed_ip(ext_port)
            return
        except Exception:
            delete_runtime_properties(ctx, RUNTIME_PROPERTIES_KEYS)
            raise
    ctx.logger.info('[all connected nodes]INFO: {0}'.format(str(ctx.capabilities.get_all().values())))
    net_id = get_openstack_id_of_single_connected_node_by_openstack_type(
        ctx, NETWORK_OPENSTACK_TYPE)

    port = {
        'name': get_resource_id(ctx, PORT_OPENSTACK_TYPE),
        'network_id': net_id,
        'security_groups': [],
    }

    _handle_fixed_ips(port)
    port.update(ctx.node.properties['port'])
    transform_resource_name(ctx, port)

    p = neutron_client.create_port({'port': port})['port']
    ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY] = p['id']
    ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY] =\
        PORT_OPENSTACK_TYPE
    ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY] = p['name']
    ctx.instance.runtime_properties[FIXED_IP_ADDRESS_PROPERTY] = \
        _get_fixed_ip(p)


@operation
@with_neutron_client
def delete(neutron_client, **kwargs):
    try:
        delete_resource_and_runtime_properties(ctx, neutron_client,
                                               RUNTIME_PROPERTIES_KEYS)
    except neutron_exceptions.NeutronClientException, e:
        if e.status_code == 404:
            # port was probably deleted when an attached device was deleted
            delete_runtime_properties(ctx, RUNTIME_PROPERTIES_KEYS)
        else:
            raise


@operation
@with_neutron_client
def detach(neutron_client, **kwargs):

    if is_external_relationship(ctx):
        ctx.logger.info('Not detaching port from server since '
                        'external port and server are being used')
        return

    port_id = ctx.target.instance.runtime_properties[OPENSTACK_ID_PROPERTY]
    server_id = ctx.source.instance.runtime_properties[OPENSTACK_ID_PROPERTY]

    server_floating_ip = _get_server_floating_ip(neutron_client, server_id)
    if server_floating_ip:
        return ctx.operation.retry(
            message='Waiting for the floating ip {0} to '
                    'detach from server {1}..'
                    .format(server_floating_ip['floating_ip_address'],
                            server_id),
            retry_after=10)
    change = {
        'port': {
            'device_id': '',
            'device_owner': ''
        }
    }
    ctx.logger.info('Detaching port {0}...'.format(port_id))
    neutron_client.update_port(port_id, change)
    ctx.logger.info('Successfully detached port {0}'.format(port_id))


@operation
@with_neutron_client
def connect_security_group(neutron_client, **kwargs):
    port_id = ctx.source.instance.runtime_properties[OPENSTACK_ID_PROPERTY]
    security_group_id = ctx.target.instance.runtime_properties[
        OPENSTACK_ID_PROPERTY]

    if is_external_relationship(ctx):
        ctx.logger.info('Validating external port and security-group are '
                        'connected')
        if any(sg for sg in neutron_client.show_port(port_id)['port'].get(
                'security_groups', []) if sg == security_group_id):
            return
        raise NonRecoverableError(
            'Expected external resources port {0} and security-group {1} to '
            'be connected'.format(port_id, security_group_id))

    # WARNING: non-atomic operation
    port = neutron_client.cosmo_get('port', id=port_id)
    ctx.logger.info(
        "connect_security_group(): source_id={0} target={1}".format(
            port_id, ctx.target.instance.runtime_properties))
    sgs = port['security_groups'] + [security_group_id]
    neutron_client.update_port(port_id, {'port': {'security_groups': sgs}})

    # Double check if SG has been actually updated (a race-condition
    # in OpenStack):
    port_info = neutron_client.show_port(port_id)['port']
    port_security_groups = port_info.get('security_groups', [])
    if security_group_id not in port_security_groups:
        return ctx.operation.retry(
            message='Security group connection (`{0}\' -> `{1}\')'
                    ' has not been established!'.format(port_id,
                                                        security_group_id),
            retry_after=_NO_SG_PORT_CONNECTION_RETRY_INTERVAL
        )


@operation
@with_neutron_client
def creation_validation(neutron_client, **kwargs):
    validate_resource(ctx, neutron_client, PORT_OPENSTACK_TYPE)


def _get_server_floating_ip(neutron_client, server_id):

    floating_ips = neutron_client.list_floatingips()

    floating_ips = floating_ips.get('floatingips')
    if not floating_ips:
        return None

    for floating_ip in floating_ips:
        port_id = floating_ip.get('port_id')
        if not port_id:
            # this floating ip is not attached to any port
            continue

        port = neutron_client.show_port(port_id)['port']
        device_id = port.get('device_id')
        if not device_id:
            # this port is not attached to any server
            continue

        if server_id == device_id:
            return floating_ip
    return None


def _get_fixed_ip(port):
    # a port may have no fixed IP if it's set on a network without subnets
    return port['fixed_ips'][0]['ip_address'] if port['fixed_ips'] else None


def _handle_fixed_ips(port):
    fixed_ips_element = {}

    # checking for fixed ip property
    if ctx.node.properties['fixed_ip']:
        fixed_ips_element['ip_address'] = ctx.node.properties['fixed_ip']

    # checking for a connected subnet
    subnet_id = get_openstack_id_of_single_connected_node_by_openstack_type(
        ctx, SUBNET_OPENSTACK_TYPE, if_exists=True)
    if subnet_id:
        fixed_ips_element['subnet_id'] = subnet_id

    # applying fixed ip parameter, if available
    if fixed_ips_element:
        port['fixed_ips'] = [fixed_ips_element]
