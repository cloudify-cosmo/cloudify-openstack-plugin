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
    subnet = {
        'name': ctx.node_id,
        'network_id': ctx.capabilities['external_id'],
    }
    subnet.update(ctx.properties['subnet'])

    s = neutron_client.create_subnet({'subnet': subnet})['subnet']
    ctx.runtime_properties['external_id'] = s['id']


@operation
@with_neutron_client
def delete(ctx, neutron_client, **kwargs):
    neutron_client.delete_subnet(ctx.runtime_properties['external_id'])
