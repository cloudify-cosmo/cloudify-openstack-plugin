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

from openstack_plugin_common import (
    transform_resource_name,
    with_neutron_client,
    get_default_resource_id,
    get_openstack_id_of_single_connected_node_by_openstack_type,
    OPENSTACK_ID_PROPERTY
)

from neutron_plugin.network import NETWORK_OPENSTACK_TYPE

PORT_OPENSTACK_TYPE = 'port'

# Runtime properties
RUNTIME_PROPERTIES_KEYS = [OPENSTACK_ID_PROPERTY]


@operation
@with_neutron_client
def create(neutron_client, **kwargs):
    net_id = get_openstack_id_of_single_connected_node_by_openstack_type(
        ctx, NETWORK_OPENSTACK_TYPE)
    port = {
        'name': get_default_resource_id(ctx, PORT_OPENSTACK_TYPE),
        'network_id': net_id,
        'security_groups': [],
    }
    port.update(ctx.properties['port'])
    transform_resource_name(ctx, port)
    p = neutron_client.create_port({'port': port})['port']
    ctx.runtime_properties[OPENSTACK_ID_PROPERTY] = p['id']


@operation
@with_neutron_client
def delete(neutron_client, **kwargs):
    neutron_client.delete_port(ctx.runtime_properties[OPENSTACK_ID_PROPERTY])

    for runtime_prop_key in RUNTIME_PROPERTIES_KEYS:
        del ctx.runtime_properties[runtime_prop_key]


@operation
@with_neutron_client
def connect_security_group(neutron_client, **kwargs):
    # WARNING: non-atomic operation
    port = neutron_client.cosmo_get(
        'port', id=ctx.runtime_properties[OPENSTACK_ID_PROPERTY])
    ctx.logger.info(
        "connect_security_group(): id={0} related={1}".format(
            ctx.runtime_properties[OPENSTACK_ID_PROPERTY],
            ctx.related.runtime_properties))
    sgs = port['security_groups']\
        + [ctx.related.runtime_properties[OPENSTACK_ID_PROPERTY]]
    neutron_client.update_port(ctx.runtime_properties[OPENSTACK_ID_PROPERTY],
                               {'port': {'security_groups': sgs}})
