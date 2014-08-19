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
)

# Runtime properties
OPENSTACK_ID_PROPERTY = 'external_id'  # network's openstack id
TYPE_NAME_PROPERTY = 'external_type'  # NOQA a property to identify the node as an openstack network node
RUNTIME_PROPERTIES_KEYS = [OPENSTACK_ID_PROPERTY, TYPE_NAME_PROPERTY]


@operation
@with_neutron_client
def create(neutron_client, **kwargs):
    network = {
        'admin_state_up': True,
        'name': ctx.node_id,
    }
    network.update(ctx.properties['network'])
    transform_resource_name(network)

    net = neutron_client.create_network({'network': network})['network']
    ctx.runtime_properties[OPENSTACK_ID_PROPERTY] = net['id']
    ctx.runtime_properties[TYPE_NAME_PROPERTY] = 'network'


@operation
@with_neutron_client
def start(neutron_client, **kwargs):
    neutron_client.update_network(
        ctx.runtime_properties[OPENSTACK_ID_PROPERTY], {
            'network': {
                'admin_state_up': True
            }
        })


@operation
@with_neutron_client
def stop(neutron_client, **kwargs):
    neutron_client.update_network(
        ctx.runtime_properties[OPENSTACK_ID_PROPERTY], {
            'network': {
                'admin_state_up': False
            }
        })


@operation
@with_neutron_client
def delete(neutron_client, **kwargs):
    neutron_client.delete_network(
        ctx.runtime_properties[OPENSTACK_ID_PROPERTY])

    for runtime_prop_key in RUNTIME_PROPERTIES_KEYS:
        del ctx.runtime_properties[runtime_prop_key]
