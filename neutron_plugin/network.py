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
    is_external_resource,
    is_external_resource_not_conditionally_created,
    delete_resource_and_runtime_properties,
    use_external_resource,
    validate_resource,
    create_object_dict,
    get_openstack_id,
    set_neutron_runtime_properties,
    add_list_to_runtime_properties,
    COMMON_RUNTIME_PROPERTIES_KEYS,
    with_resume_flags
)

NETWORK_OPENSTACK_TYPE = 'network'
ADMIN_STATE_UP = 'admin_state_up'

# Runtime properties
RUNTIME_PROPERTIES_KEYS = COMMON_RUNTIME_PROPERTIES_KEYS


@operation(resumable=True)
@with_resume_flags
@with_neutron_client
def create(neutron_client, args, **kwargs):

    if use_external_resource(ctx, neutron_client, NETWORK_OPENSTACK_TYPE):
        return
    network = create_object_dict(ctx,
                                 NETWORK_OPENSTACK_TYPE,
                                 args,
                                 {ADMIN_STATE_UP: True})

    net = neutron_client.create_network(
        {NETWORK_OPENSTACK_TYPE: network})[NETWORK_OPENSTACK_TYPE]
    set_neutron_runtime_properties(ctx, net, NETWORK_OPENSTACK_TYPE)


@operation(resumable=True)
@with_resume_flags
@with_neutron_client
def start(neutron_client, **kwargs):
    network_id = get_openstack_id(ctx)

    if is_external_resource_not_conditionally_created(ctx):
        ctx.logger.info('Validating external network is started')
        if not neutron_client.show_network(
                network_id)[NETWORK_OPENSTACK_TYPE][ADMIN_STATE_UP]:
            raise NonRecoverableError(
                'Expected external resource network {0} to be in '
                '"admin_state_up"=True'.format(network_id))
        return

    neutron_client.update_network(
        network_id, {
            NETWORK_OPENSTACK_TYPE: {
                ADMIN_STATE_UP: True
            }
        })


@operation(resumable=True)
@with_resume_flags
@with_neutron_client
def stop(neutron_client, **kwargs):
    if is_external_resource(ctx):
        ctx.logger.info('Not stopping network since an external network is '
                        'being used')
        return

    neutron_client.update_network(get_openstack_id(ctx), {
            NETWORK_OPENSTACK_TYPE: {
                ADMIN_STATE_UP: False
            }
        })


@operation(resumable=True)
@with_resume_flags
@with_neutron_client
def delete(neutron_client, **kwargs):
    delete_resource_and_runtime_properties(ctx, neutron_client,
                                           RUNTIME_PROPERTIES_KEYS)


@operation(resumable=True)
@with_resume_flags
@with_neutron_client
def list_networks(neutron_client, args, **kwargs):
    net_list = neutron_client.list_networks(**args)
    add_list_to_runtime_properties(ctx,
                                   NETWORK_OPENSTACK_TYPE,
                                   net_list.get('networks', []))


@operation(resumable=True)
@with_resume_flags
@with_neutron_client
def creation_validation(neutron_client, **kwargs):
    validate_resource(ctx, neutron_client, NETWORK_OPENSTACK_TYPE)
