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

import netaddr

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from IPy import IP

import neutronclient.common.exceptions as neutron_exceptions
from openstack_plugin_common import (
    with_neutron_client,
    with_nova_client,
    get_openstack_id_of_single_connected_node_by_openstack_type,
    get_openstack_ids_of_connected_nodes_by_openstack_type,
    delete_resource_and_runtime_properties,
    delete_runtime_properties,
    use_external_resource,
    is_external_relationship,
    add_list_to_runtime_properties,
    validate_resource,
    get_openstack_id,
    set_neutron_runtime_properties,
    create_object_dict,
    COMMON_RUNTIME_PROPERTIES_KEYS,
    is_external_relationship_not_conditionally_created,
    with_resume_operation)

from neutron_plugin.network import NETWORK_OPENSTACK_TYPE
from neutron_plugin.subnet import SUBNET_OPENSTACK_TYPE
from neutron_plugin.security_group import SG_OPENSTACK_TYPE
from openstack_plugin_common.floatingip import get_server_floating_ip

PORT_OPENSTACK_TYPE = 'port'
PORT_ALLOWED_ADDRESS = 'allowed_address_pairs'
PORT_ADDRESS_REL_TYPE = 'cloudify.openstack.port_connected_to_floating_ip'

# Runtime properties
FIXED_IP_ADDRESS_PROPERTY = 'fixed_ip_address'  # the fixed ip address
MAC_ADDRESS_PROPERTY = 'mac_address'  # the mac address
# List of all ip addresses exported as runtime properties for port instance
IPS_ADDRESS_PROPERTIES = [
    'ipv4_addresses',
    'ipv6_addresses',
    'ipv4_address',
    'ipv6_address'
]
PORT_IPS_PROPERTIES = [FIXED_IP_ADDRESS_PROPERTY, MAC_ADDRESS_PROPERTY]\
                      + IPS_ADDRESS_PROPERTIES
RUNTIME_PROPERTIES_KEYS = COMMON_RUNTIME_PROPERTIES_KEYS + PORT_IPS_PROPERTIES

NO_SG_PORT_CONNECTION_RETRY_INTERVAL = 3


def _port_update(neutron_client, port_id, args, ext_port):
    runtime_properties = ctx.instance.runtime_properties
    updated_params = create_object_dict(ctx, PORT_OPENSTACK_TYPE, args, {})
    if updated_params:
        if PORT_ALLOWED_ADDRESS in updated_params:
            allowed_addpairs = ext_port.get(PORT_ALLOWED_ADDRESS, [])
            for allowed_addpair in updated_params[PORT_ALLOWED_ADDRESS]:
                for old_addpair in allowed_addpairs:
                    old_ip = old_addpair.get('ip_address')
                    if old_ip == allowed_addpair.get('ip_address'):
                        raise NonRecoverableError(
                            'Ip {} is already assigned to {}.'
                            .format(old_ip, port_id))
                else:
                    allowed_addpairs.append(allowed_addpair)

            change = {
                PORT_OPENSTACK_TYPE: {
                    PORT_ALLOWED_ADDRESS: allowed_addpairs
                }
            }
            neutron_client.update_port(port_id, change)
            runtime_properties[PORT_ALLOWED_ADDRESS] = allowed_addpairs
            ctx.logger.info("Applied: {}".format(repr(change)))
    # update network id
    net_id = get_openstack_id_of_single_connected_node_by_openstack_type(
            ctx, NETWORK_OPENSTACK_TYPE, True)
    if net_id:
        if neutron_client.show_port(
                port_id)[PORT_OPENSTACK_TYPE]['network_id'] != net_id:
            raise NonRecoverableError(
                'Expected external resources port {0} and network {1} '
                'to be connected'.format(port_id, net_id))
    # update port ip and mac
    runtime_properties[FIXED_IP_ADDRESS_PROPERTY] = _get_fixed_ip(ext_port)
    runtime_properties[MAC_ADDRESS_PROPERTY] = ext_port['mac_address']


def _get_ips_from_port(port):
    """
    This method will extract ipv4 & ipv6 for from port object
    :param port:
    :return:
    """
    net_ips = port['fixed_ips'] if port.get('fixed_ips') else []
    ips_v4 = []
    ips_v6 = []
    for net_ip in net_ips:
        if net_ip.get('ip_address'):
            ip_address = net_ip['ip_address']
            try:
                # Lookup all ipv4s
                IP(ip_address, ipversion=4)
                ips_v4.append(ip_address)
            except ValueError:
                # If it is not an ipv4 then collect the ipv6
                IP(ip_address, ipversion=6)
                ips_v6.append(ip_address)
    return ips_v4, ips_v6


def _export_ips_to_port_instance(port):
    """
    This method will export ips of the current port as runtime properties
    for port node instance to be access later on
    :param port:
    """
    ips_v4, ips_v6 = _get_ips_from_port(port)
    # Set list of ipv4 for the current nod as runtime properties
    ctx.instance.runtime_properties['ipv4_addresses'] = ips_v4
    # # Set list of ipv6 for the current nod as runtime properties
    ctx.instance.runtime_properties['ipv6_addresses'] = ips_v6

    if len(ips_v4) == 1:
        ctx.instance.runtime_properties['ipv4_address'] = ips_v4[0]
    else:
        ctx.instance.runtime_properties['ipv4_address'] = ''

    if len(ips_v6) == 1:
        ctx.instance.runtime_properties['ipv6_address'] = ips_v6[0]
    else:
        ctx.instance.runtime_properties['ipv6_address'] = ''


@operation(resumable=True)
@with_resume_operation
@with_neutron_client
def create(neutron_client, args, **kwargs):

    ext_port = use_external_resource(ctx, neutron_client, PORT_OPENSTACK_TYPE)
    if ext_port:
        try:
            port_id = get_openstack_id(ctx)
            _port_update(neutron_client, port_id, args, ext_port)
            return
        except Exception:
            delete_runtime_properties(ctx, RUNTIME_PROPERTIES_KEYS)
            raise

    net_id = ctx.node.properties.get(
        PORT_OPENSTACK_TYPE, {}).get('network_id')
    if not net_id:
        net_id = \
            get_openstack_id_of_single_connected_node_by_openstack_type(
                ctx, NETWORK_OPENSTACK_TYPE)

    port = create_object_dict(ctx,
                              PORT_OPENSTACK_TYPE,
                              args,
                              {'network_id': net_id})
    _handle_fixed_ips(port, neutron_client)
    _handle_security_groups(port)

    p = neutron_client.create_port(
        {PORT_OPENSTACK_TYPE: port})[PORT_OPENSTACK_TYPE]

    set_neutron_runtime_properties(ctx, p, PORT_OPENSTACK_TYPE)
    ctx.instance.runtime_properties[FIXED_IP_ADDRESS_PROPERTY] = \
        _get_fixed_ip(p)
    ctx.instance.runtime_properties[MAC_ADDRESS_PROPERTY] = p['mac_address']
    # Export ip addresses attached to port as runtime properties
    _export_ips_to_port_instance(p)


@operation(resumable=True)
@with_resume_operation
@with_nova_client
@with_neutron_client
def attach(nova_client, neutron_client, **kwargs):
    if is_external_relationship(ctx):
        ctx.logger.info('Not attaching port from server since '
                        'external port and server are being used')
        return

    server_id = get_openstack_id(ctx.source)
    port_id = get_openstack_id(ctx.target)
    port = neutron_client.show_port(port_id)

    # If port is attached to floating ip then once the port is attached to
    # the server, the floating ip will be assigned to the server directly,
    # in case of healing/deployment update it is not necessary to attach
    # floating ip associated with assigned port to server and will raise
    # error in since the port is not yet attached the server in case of
    # healing/deployment update the port
    change = {
        PORT_OPENSTACK_TYPE: {
            'device_id': server_id,
        }
    }
    device_id = port['port'].get('device_id')
    if not device_id or device_id != server_id:
        ctx.logger.info('Attaching port {0}...'.format(port_id))
        neutron_client.update_port(port_id, change)
        ctx.logger.info('Successfully attached port {0}'.format(port_id))
    else:
        ctx.logger.info(
            'Skipping port {0} attachment, '
            'because it is already attached '
            'to device (server) id {1}.'.format(port_id, device_id))


def _port_delete(neutron_client, port_id, ext_port):
    updated_params = ctx.node.properties.get(PORT_OPENSTACK_TYPE)
    if updated_params:
        if PORT_ALLOWED_ADDRESS in updated_params:
            ips_for_remove = []
            updated_pairs = []
            allowed_addpairs = ext_port.get(PORT_ALLOWED_ADDRESS, [])
            # ip's for remove
            for allowed_addpair in updated_params[PORT_ALLOWED_ADDRESS]:
                ips_for_remove.append(allowed_addpair.get('ip_address'))
            # cleanup ip's
            for old_addpair in allowed_addpairs:
                old_ip = old_addpair.get('ip_address')
                if old_ip not in ips_for_remove:
                    updated_pairs.append(old_addpair)
            # apply changes
            change = {
                PORT_OPENSTACK_TYPE: {
                    PORT_ALLOWED_ADDRESS: updated_pairs
                }
            }
            neutron_client.update_port(port_id, change)
            ctx.logger.info("Applied on remove: {}".format(repr(change)))


@operation(resumable=True)
@with_resume_operation
@with_neutron_client
def delete(neutron_client, **kwargs):
    try:
        # clean up external resource
        ext_port = use_external_resource(ctx, neutron_client,
                                         PORT_OPENSTACK_TYPE)
        if ext_port:
            port_id = get_openstack_id(ctx)
            _port_delete(neutron_client, port_id, ext_port)
        # remove port if need
        delete_resource_and_runtime_properties(ctx, neutron_client,
                                               RUNTIME_PROPERTIES_KEYS)
    except neutron_exceptions.NeutronClientException as e:
        if e.status_code == 404:
            # port was probably deleted when an attached device was deleted
            delete_runtime_properties(ctx, RUNTIME_PROPERTIES_KEYS)
        else:
            raise


@operation(resumable=True)
@with_resume_operation
@with_nova_client
@with_neutron_client
def detach(nova_client, neutron_client, **kwargs):
    if is_external_relationship(ctx):
        ctx.logger.info('Not detaching port from server since '
                        'external port and server are being used')
        return

    port_id = get_openstack_id(ctx.target)
    server_id = get_openstack_id(ctx.source)

    server_floating_ip = get_server_floating_ip(neutron_client, server_id)
    if server_floating_ip:
        ctx.logger.info('We have floating ip {0} attached to server'
                        .format(server_floating_ip['floating_ip_address']))
        server = nova_client.servers.get(server_id)
        try:
            server.remove_floating_ip(
                server_floating_ip['floating_ip_address'])
        except AttributeError:
            # To support version mismatch.
            neutron_client.update_floatingip(
                server_floating_ip['id'], {'floatingip': {'port_id': None}})
        return ctx.operation.retry(
            message='Waiting for the floating ip {0} to '
                    'detach from server {1}..'
                    .format(server_floating_ip['floating_ip_address'],
                            server_id),
            retry_after=10)
    change = {
        PORT_OPENSTACK_TYPE: {
            'device_id': '',
            'device_owner': ''
        }
    }
    ctx.logger.info('Detaching port {0}...'.format(port_id))
    neutron_client.update_port(port_id, change)
    ctx.logger.info('Successfully detached port {0}'.format(port_id))


@operation(resumable=True)
@with_resume_operation
@with_neutron_client
def connect_security_group(neutron_client, **kwargs):
    port_id = get_openstack_id(ctx.source)
    security_group_id = get_openstack_id(ctx.target)

    if is_external_relationship_not_conditionally_created(ctx):
        ctx.logger.info('Validating external port and security-group are '
                        'connected')
        if any(sg for sg in neutron_client.show_port(port_id)['port'].get(
                'security_groups', []) if sg == security_group_id):
            return
        raise NonRecoverableError(
            'Expected external resources port {0} and security-group {1} to '
            'be connected'.format(port_id, security_group_id))

    # WARNING: non-atomic operation
    port = neutron_client.cosmo_get(PORT_OPENSTACK_TYPE, id=port_id)
    ctx.logger.info(
        "connect_security_group(): source_id={0} target={1}".format(
            port_id, ctx.target.instance.runtime_properties))
    # We could just pass the port['security_groups']
    # dict here with a new element, however we need to test
    # a race condition in Openstack so we need to copy the security
    # group list.
    sgs = port['security_groups'][:]
    if security_group_id not in port['security_groups']:
        sgs.append(security_group_id)
    neutron_client.update_port(port_id,
                               {PORT_OPENSTACK_TYPE: {'security_groups': sgs}})

    # Double check if SG has been actually updated (a race-condition
    # in OpenStack):
    port_info = neutron_client.show_port(port_id)['port']
    port_security_groups = port_info.get('security_groups', [])
    if security_group_id not in port_security_groups:
        return ctx.operation.retry(
            message='Security group connection (`{0}\' -> `{1}\')'
                    ' has not been established!'.format(port_id,
                                                        security_group_id),
            retry_after=NO_SG_PORT_CONNECTION_RETRY_INTERVAL
        )


@operation(resumable=True)
@with_resume_operation
@with_neutron_client
def disconnect_security_group(neutron_client, **kwargs):
    port_id = get_openstack_id(ctx.source)
    security_group_id = get_openstack_id(ctx.target)

    if is_external_relationship_not_conditionally_created(ctx):
        ctx.logger.info(
            'Port {0} and Security Group {1} are external resources. '
            'Not performing disconnect.')
        return

    port = neutron_client.cosmo_get(PORT_OPENSTACK_TYPE, id=port_id)
    sgs = port['security_groups'][:]
    if security_group_id not in port['security_groups']:
        return
    sgs.remove(security_group_id)
    neutron_client.update_port(port_id,
                               {PORT_OPENSTACK_TYPE: {'security_groups': sgs}})
    port_info = neutron_client.show_port(port_id)['port']
    port_security_groups = port_info.get('security_groups', [])
    if security_group_id in port_security_groups:
        return ctx.operation.retry(
            message='Security group connection (`{0}\' -> `{1}\')'
                    ' has not been established!'.format(port_id,
                                                        security_group_id),
            retry_after=NO_SG_PORT_CONNECTION_RETRY_INTERVAL
        )


@operation(resumable=True)
@with_resume_operation
@with_neutron_client
def list_ports(neutron_client, args, **kwargs):
    port_list = neutron_client.list_ports(**args)
    add_list_to_runtime_properties(ctx,
                                   PORT_OPENSTACK_TYPE,
                                   port_list.get('ports', []))


@operation(resumable=True)
@with_resume_operation
@with_neutron_client
def creation_validation(neutron_client, **kwargs):
    validate_resource(ctx, neutron_client, PORT_OPENSTACK_TYPE)


def _get_fixed_ip(port):
    # a port may have no fixed IP if it's set on a network without subnets
    return port['fixed_ips'][0]['ip_address'] if port['fixed_ips'] else None


def _valid_subnet_ip(ip_address, subnet_dict):
    """Check if ip_address is valid for subnet_dict['cidr']

    :param ip_address: string
    :param subnet_dict: dict with 'cidr' string
    :return: bool
    """

    try:
        cidr = subnet_dict.get('subnet', {}).get('cidr')
        ctx.logger.debug('Check ip {ip_address} in subnet {cidr}'.format(
            ip_address=repr(ip_address),
            cidr=repr(cidr)))
        if netaddr.IPAddress(ip_address) in netaddr.IPNetwork(cidr):
            return True
    except TypeError:
        pass
    return False


def _handle_fixed_ips(port, neutron_client):
    """Combine IPs and Subnets for the Port fixed IPs list.

    The Port object looks something this:
    {
      'port': {
        'id': 'some-id',
        'fixed_ips': [
          {'subnet_id': 'subnet1', 'ip_address': '1.2.3.4'},
          {'ip_address': '1.2.3.5'},
          {'subnet_id': 'subnet3'},
        ]
      ...snip...
    }

    We need to combine subnets and ips from three sources:
    1) Fixed IPs and Subnets from the Port object.
    2) Subnets from relationships to subnets.
    3) A Fixed IP from node properties.

    There are some issues:
    1) Users can provide both subnets and relationships to subnets.
    2) Recurrences of the subnet_id indicate a desire
       for multiple IPs on that subnet.
    3) If we provide a fixed_ip, we don't also know the
       target subnet because of how the node properties are.
       We should change that.
       Have not yet changed that.
       But will need to support both paths anyway.

    :param port: An Openstack API Port Object.
    :param neutron_client: Openstack Neutron Client.
    :return: None
    """

    fixed_ips = port.get('fixed_ips', [])
    subnet_ids_from_port = [net.get('subnet_id') for net in fixed_ips]
    subnet_ids_from_rels = \
        get_openstack_ids_of_connected_nodes_by_openstack_type(
            ctx, SUBNET_OPENSTACK_TYPE)

    # Add the subnets from relationships to the port subnets.
    for subnet_from_rel in subnet_ids_from_rels:
        if subnet_from_rel not in subnet_ids_from_port:
            fixed_ips.append({'subnet_id': subnet_from_rel})

    addresses = [ip.get('ip_address') for ip in fixed_ips]
    fixed_ip_from_props = ctx.node.properties['fixed_ip']

    # If we have a fixed_ip from node props, we need to add it,
    # but first try to match it with one of our subnets.
    # The fixed_ip_element should be one of:
    # 1) {'ip_address': 'x.x.x.x'}
    # 2) {'subnet_id': '....'}
    # 3) {'ip_address': 'x.x.x.x', 'subnet_id': '....'}
    # show_subnet returns something like this:
    # subnet = {
    #   'subnet': {
    #     'id': 'subnet1',
    #     'cidr': '1.2.3.4/24',
    #     'allocation_pools': [],
    #     ...snip...
    #   }
    # }
    if fixed_ip_from_props and not (fixed_ip_from_props in addresses):
        fixed_ip_element = {'ip_address': fixed_ip_from_props}
        for fixed_ip in fixed_ips:
            subnet_id = fixed_ip.get('subnet_id')
            if not _valid_subnet_ip(
                    fixed_ip_from_props,
                    neutron_client.show_subnet(subnet_id)):
                continue
            fixed_ip_element['subnet_id'] = subnet_id
            del fixed_ips[fixed_ips.index(fixed_ip)]
            break
        fixed_ips.append(fixed_ip_element)

    # Finally update the object.
    if fixed_ips:
        port['fixed_ips'] = fixed_ips


def _handle_security_groups(port):
    security_groups = get_openstack_ids_of_connected_nodes_by_openstack_type(
        ctx, SG_OPENSTACK_TYPE)
    if security_groups:
        port['security_groups'] = security_groups
