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

from cloudify.decorators import operation
from openstack_plugin_common import (
    transform_resource_name,
    with_neutron_client,
)


def _find_network_in_related_nodes(ctx, neutron_client):
    networks_ids = [n['id'] for n in
                    neutron_client.list_networks()['networks']]
    ret = []
    for runtime_properties in ctx.capabilities.get_all().values():
        external_id = runtime_properties.get('external_id')
        if external_id in networks_ids:
            ret.append(external_id)
    if len(ret) != 1:
        # TODO: better message
        raise RuntimeError("Failed to find port's network")
    return ret[0]


@operation
@with_neutron_client
def create(ctx, neutron_client, **kwargs):
    port = {
        'name': ctx.node_id,
        'network_id': _find_network_in_related_nodes(ctx, neutron_client),
        'security_groups': [],
    }
    port.update(ctx.properties['port'])
    transform_resource_name(port, ctx)
    p = neutron_client.create_port({'port': port})['port']
    ctx.runtime_properties['external_id'] = p['id']


@operation
@with_neutron_client
def delete(ctx, neutron_client, **kwargs):
    neutron_client.delete_port(ctx.runtime_properties['external_id'])


@operation
@with_neutron_client
def connect_security_group(ctx, neutron_client, **kwargs):
    # WARNING: non-atomic operation
    port = neutron_client.cosmo_get('port',
                                    id=ctx.runtime_properties['external_id'])
    ctx.logger.info(
        "connect_security_group(): id={0} related={1}".format(
            ctx.runtime_properties['external_id'],
            ctx.related.runtime_properties))
    sgs = port['security_groups']\
        + [ctx.related.runtime_properties['external_id']]
    neutron_client.update_port(ctx.runtime_properties['external_id'],
                               {'port': {'security_groups': sgs}})
