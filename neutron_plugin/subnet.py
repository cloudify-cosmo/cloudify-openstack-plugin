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
    get_openstack_id_of_single_connected_node_by_openstack_type,
    delete_resource_and_runtime_properties,
    delete_runtime_properties,
    use_external_resource,
    validate_resource,
    validate_ip_or_range_syntax,
    create_object_dict,
    get_openstack_id,
    set_neutron_runtime_properties,
    add_list_to_runtime_properties,
    COMMON_RUNTIME_PROPERTIES_KEYS,
    with_resume_flags
)

from neutron_plugin.network import NETWORK_OPENSTACK_TYPE

SUBNET_OPENSTACK_TYPE = 'subnet'
NETWORK_ID = 'network_id'
CIDR = 'cidr'

# Runtime properties
RUNTIME_PROPERTIES_KEYS = COMMON_RUNTIME_PROPERTIES_KEYS


@operation(resumable=True)
@with_resume_flags
@with_neutron_client
def create(neutron_client, args, **kwargs):

    if use_external_resource(ctx, neutron_client, SUBNET_OPENSTACK_TYPE):
        try:
            net_id = \
                get_openstack_id_of_single_connected_node_by_openstack_type(
                    ctx, NETWORK_OPENSTACK_TYPE, True)

            if net_id:
                subnet_id = get_openstack_id(ctx)

                if neutron_client.show_subnet(
                        subnet_id)[SUBNET_OPENSTACK_TYPE][NETWORK_ID] \
                        != net_id:
                    raise NonRecoverableError(
                        'Expected external resources subnet {0} and network'
                        ' {1} to be connected'.format(subnet_id, net_id))
            return
        except Exception:
            delete_runtime_properties(ctx, RUNTIME_PROPERTIES_KEYS)
            raise

    net_id = get_openstack_id_of_single_connected_node_by_openstack_type(
        ctx, NETWORK_OPENSTACK_TYPE)
    subnet = create_object_dict(ctx,
                                SUBNET_OPENSTACK_TYPE,
                                args,
                                {NETWORK_ID: net_id})

    s = neutron_client.create_subnet(
        {SUBNET_OPENSTACK_TYPE: subnet})[SUBNET_OPENSTACK_TYPE]
    set_neutron_runtime_properties(ctx, s, SUBNET_OPENSTACK_TYPE)


@operation(resumable=True)
@with_resume_flags
@with_neutron_client
def delete(neutron_client, **kwargs):
    delete_resource_and_runtime_properties(ctx, neutron_client,
                                           RUNTIME_PROPERTIES_KEYS)


@operation(resumable=True)
@with_resume_flags
@with_neutron_client
def list_subnets(neutron_client, args, **kwargs):
    subnet_list = neutron_client.list_subnets(**args)
    add_list_to_runtime_properties(ctx,
                                   SUBNET_OPENSTACK_TYPE,
                                   subnet_list.get('subnets', []))


@operation(resumable=True)
@with_resume_flags
@with_neutron_client
def creation_validation(neutron_client, args, **kwargs):
    validate_resource(ctx, neutron_client, SUBNET_OPENSTACK_TYPE)
    subnet = dict(ctx.node.properties[SUBNET_OPENSTACK_TYPE], **args)

    if CIDR not in subnet:
        err = '"cidr" property must appear under the "subnet" property of a ' \
              'subnet node'
        ctx.logger.error('VALIDATION ERROR: ' + err)
        raise NonRecoverableError(err)
    validate_ip_or_range_syntax(ctx, subnet[CIDR])
