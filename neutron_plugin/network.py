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
from openstack_plugin_common import with_neutron_client


@operation
@with_neutron_client
def create(ctx, neutron_client, **kwargs):
    network = {
        'admin_state_up': True,
        'name': ctx.node_id,
    }
    network.update(ctx.properties['network'])

    net = neutron_client.create_network({'network': network})['network']
    ctx['external_id'] = net['id']
    ctx.update()


@operation
@with_neutron_client
def start(ctx, neutron_client, **kwargs):
    neutron_client.update_network(ctx.runtime_properties['external_id'], {
        'network': {
            'admin_state_up': True
        }
    })


@operation
@with_neutron_client
def stop(ctx, neutron_client, **kwargs):
    neutron_client.update_network(ctx.runtime_properties['external_id'], {
        'network': {
            'admin_state_up': False
        }
    })


@operation
@with_neutron_client
def delete(ctx, neutron_client, **kwargs):
    neutron_client.delete_network(ctx.runtime_properties['external_id'])
