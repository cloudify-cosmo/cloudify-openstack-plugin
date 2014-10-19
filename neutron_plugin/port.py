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
    OPENSTACK_ID_PROPERTY,
    OPENSTACK_TYPE_PROPERTY,
    OPENSTACK_NAME_PROPERTY,
    COMMON_RUNTIME_PROPERTIES_KEYS
)

from neutron_plugin.network import NETWORK_OPENSTACK_TYPE

PORT_OPENSTACK_TYPE = 'port'

# Runtime properties
RUNTIME_PROPERTIES_KEYS = COMMON_RUNTIME_PROPERTIES_KEYS


@operation
@with_neutron_client
def create(neutron_client, **kwargs):

    if use_external_resource(ctx, neutron_client, PORT_OPENSTACK_TYPE):
        try:
            net_id = \
                get_openstack_id_of_single_connected_node_by_openstack_type(
                    ctx, PORT_OPENSTACK_TYPE, True)

            if net_id:
                port_id = ctx.instance.runtime_properties[
                    OPENSTACK_ID_PROPERTY]

                if neutron_client.show_port(
                        port_id)['port']['network_id'] != net_id:
                    raise NonRecoverableError(
                        'Expected external resources port {0} and network {1} '
                        'to be connected'.format(port_id, net_id))
            return
        except Exception:
            delete_runtime_properties(ctx, RUNTIME_PROPERTIES_KEYS)
            raise

    net_id = get_openstack_id_of_single_connected_node_by_openstack_type(
        ctx, NETWORK_OPENSTACK_TYPE)
    port = {
        'name': get_resource_id(ctx, PORT_OPENSTACK_TYPE),
        'network_id': net_id,
        'security_groups': [],
    }
    port.update(ctx.node.properties['port'])
    transform_resource_name(ctx, port)
    p = neutron_client.create_port({'port': port})['port']
    ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY] = p['id']
    ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY] =\
        PORT_OPENSTACK_TYPE
    ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY] = p['name']


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
