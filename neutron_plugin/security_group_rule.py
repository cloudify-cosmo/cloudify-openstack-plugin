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

__author__ = 'ran'

import re

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from openstack_plugin_common import (
    with_neutron_client,
    get_openstack_id_of_single_connected_node_by_openstack_type,
    OPENSTACK_ID_PROPERTY
)

from neutron_plugin.security_group import SECURITY_GROUP_OPENSTACK_TYPE

NODE_NAME_RE = re.compile('^(.*)_.*$')  # Anything before last underscore

# Runtime properties
RUNTIME_PROPERTIES_KEYS = [OPENSTACK_ID_PROPERTY]


@operation
@with_neutron_client
def create(neutron_client, **kwargs):
    sgr = _process_rule(ctx.properties['security_group_rule'], neutron_client)

    sg_id = get_openstack_id_of_single_connected_node_by_openstack_type(
        SECURITY_GROUP_OPENSTACK_TYPE)
    sgr['security_group_id'] = sg_id
    neutron_client.create_security_group_rule({'security_group_rule': sgr})


@operation
@with_neutron_client
def delete(neutron_client, **kwargs):
    sgr_id = ctx.runtime_properties[OPENSTACK_ID_PROPERTY]
    neutron_client.delete_security_group_rule(sgr_id)

    for runtime_prop_key in RUNTIME_PROPERTIES_KEYS:
        del ctx.runtime_properties[runtime_prop_key]


def _process_rule(rule, neutron_client):
    ctx.logger.debug(
        "Security group rule before transformations: {0}".format(rule))
    sgr = {
        'direction': 'ingress',
        'ethertype': 'IPv4',
        'port_range_max': rule.get('port', 65535),
        'port_range_min': rule.get('port', 1),
        'protocol': 'tcp',
        'remote_group_id': None,
        'remote_ip_prefix': '0.0.0.0/0',
        }
    sgr.update(rule)

    # Remove the sugaring "port" parameter
    if 'port' in sgr:
        del sgr['port']

    if ('remote_group_node' in sgr) and sgr['remote_group_node']:
        _, remote_group_node = _capabilities_of_node_named(
            sgr['remote_group_node'])
        sgr['remote_group_id'] = remote_group_node[OPENSTACK_ID_PROPERTY]
        del sgr['remote_group_node']
        del sgr['remote_ip_prefix']

    if ('remote_group_name' in sgr) and sgr['remote_group_name']:
        sgr['remote_group_id'] = neutron_client.cosmo_get_named(
            'security_group', sgr['remote_group_name'])['id']
        del sgr['remote_group_name']
        del sgr['remote_ip_prefix']

    ctx.logger.debug(
        "Security group rule after transformations: {0}".format(sgr))
    return sgr


def _capabilities_of_node_named(node_name):
    result = None
    caps = ctx.capabilities.get_all()
    for node_id in caps:
        match = NODE_NAME_RE.match(node_id)
        if match:
            candidate_node_name = match.group(1)
            if candidate_node_name == node_name:
                if result:
                    raise NonRecoverableError(
                        "More than one node named '{0}' "
                        "in capabilities".format(node_name))
                result = (node_id, caps[node_id])
    if not result:
        raise NonRecoverableError(
            "Could not find node named '{0}' "
            "in capabilities".format(node_name))
    return result
