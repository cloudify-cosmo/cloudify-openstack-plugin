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

from openstack_plugin_common import (
    with_neutron_client,
    provider,
    delete_resource_and_runtime_properties,
    use_external_resource,
    validate_resource,
    OPENSTACK_ID_PROPERTY,
    OPENSTACK_TYPE_PROPERTY,
    COMMON_RUNTIME_PROPERTIES_KEYS)

FLOATINGIP_OPENSTACK_TYPE = 'floatingip'

# Runtime properties
IP_ADDRESS_PROPERTY = 'floating_ip_address'  # the actual ip address
RUNTIME_PROPERTIES_KEYS = COMMON_RUNTIME_PROPERTIES_KEYS + \
    [IP_ADDRESS_PROPERTY]


@operation
@with_neutron_client
def create(neutron_client, **kwargs):

    external_fip = use_external_resource(
        ctx, neutron_client, FLOATINGIP_OPENSTACK_TYPE, 'floating_ip_address')
    if external_fip:
        ctx.instance.runtime_properties[IP_ADDRESS_PROPERTY] = \
            external_fip['floating_ip_address']
        return

    floatingip = {
        # No defaults
    }
    floatingip.update(ctx.node.properties['floatingip'])

    # Sugar: floating_network_name -> (resolve) -> floating_network_id
    if 'floating_network_name' in floatingip:
        floatingip['floating_network_id'] = neutron_client.cosmo_get_named(
            'network', floatingip['floating_network_name'])['id']
        del floatingip['floating_network_name']
    elif 'floating_network_id' not in floatingip:
        provider_context = provider(ctx)
        ext_network = provider_context.ext_network
        if ext_network:
            floatingip['floating_network_id'] = ext_network['id']
    else:
        raise NonRecoverableError('Missing floating network id or name')

    fip = neutron_client.create_floatingip(
        {'floatingip': floatingip})['floatingip']
    ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY] = fip['id']
    ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY] = \
        FLOATINGIP_OPENSTACK_TYPE
    ctx.instance.runtime_properties[IP_ADDRESS_PROPERTY] = \
        fip['floating_ip_address']


@operation
@with_neutron_client
def delete(neutron_client, **kwargs):
    delete_resource_and_runtime_properties(ctx, neutron_client,
                                           RUNTIME_PROPERTIES_KEYS)


@operation
@with_neutron_client
def creation_validation(neutron_client, **kwargs):
    validate_resource(ctx, neutron_client, FLOATINGIP_OPENSTACK_TYPE,
                      'floating_ip_address')
