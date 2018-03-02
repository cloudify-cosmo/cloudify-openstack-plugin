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

import copy
import re
from time import sleep

from requests.exceptions import RequestException

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from openstack_plugin_common import (
    with_neutron_client,
    create_object_dict,
    use_external_resource,
    delete_resource_and_runtime_properties,
    add_list_to_runtime_properties,
    set_neutron_runtime_properties,
    validate_resource,
    validate_ip_or_range_syntax,
    OPENSTACK_ID_PROPERTY,
    COMMON_RUNTIME_PROPERTIES_KEYS
)

DEFAULT_RULE_VALUES = {
    'direction': 'ingress',
    'ethertype': 'IPv4',
    'port_range_min': 1,
    'port_range_max': 65535,
    'protocol': 'tcp',
    'remote_group_id': None,
    'remote_ip_prefix': '0.0.0.0/0',
}


SECURITY_GROUP_OPENSTACK_TYPE = 'security_group'

# Runtime properties
RUNTIME_PROPERTIES_KEYS = COMMON_RUNTIME_PROPERTIES_KEYS

NODE_NAME_RE = re.compile('^(.*)_.*$')  # Anything before last underscore


@operation
@with_neutron_client
def create(
    neutron_client, args,
    status_attempts=10, status_timeout=2, **kwargs
):
    security_group = create_object_dict(ctx, SECURITY_GROUP_OPENSTACK_TYPE,
                                        args, {})

    if not security_group.get('description', None):
        security_group['description'] = ctx.node.properties['description']

    sg_rules = process_rules(neutron_client, DEFAULT_RULE_VALUES,
                             'remote_ip_prefix', 'remote_group_id',
                             'port_range_min', 'port_range_max')

    disable_default_egress_rules = ctx.node.properties.get(
        'disable_default_egress_rules')

    if use_external_resource(ctx,
                             neutron_client,
                             SECURITY_GROUP_OPENSTACK_TYPE):
        return

    sg = neutron_client.create_security_group(
        {SECURITY_GROUP_OPENSTACK_TYPE: security_group}
    )[SECURITY_GROUP_OPENSTACK_TYPE]

    for attempt in range(max(status_attempts, 1)):
        sleep(status_timeout)
        try:
            neutron_client.show_security_group(sg['id'])
        except RequestException as e:
            ctx.logger.debug(
                "Waiting for SG to be visible. Attempt {}"
                .format(attempt))
        else:
            break
    else:
        raise NonRecoverableError(
            "Timed out waiting for security_group to exist", e)

    set_neutron_runtime_properties(ctx, sg, SECURITY_GROUP_OPENSTACK_TYPE)

    try:
        if disable_default_egress_rules:
            for er in _egress_rules(_rules_for_sg_id(neutron_client,
                                                     sg['id'])):
                neutron_client.delete_security_group_rule(er['id'])

        for sgr in sg_rules:
            sgr['security_group_id'] = sg['id']
            neutron_client.create_security_group_rule(
                {'security_group_rule': sgr})
    except Exception:
        try:
            delete_resource_and_runtime_properties(
                ctx, neutron_client,
                RUNTIME_PROPERTIES_KEYS)
        except Exception as e:
            raise NonRecoverableError(
                'Exception while tearing down for retry', e)
        raise


@operation
@with_neutron_client
def delete(neutron_client, **kwargs):
    delete_resource_and_runtime_properties(ctx,
                                           neutron_client,
                                           RUNTIME_PROPERTIES_KEYS)


@with_neutron_client
def list_security_groups(neutron_client, args, **kwargs):
    sg_list = neutron_client.list_security_groups(**args)
    add_list_to_runtime_properties(ctx,
                                   SECURITY_GROUP_OPENSTACK_TYPE,
                                   sg_list.get('security_groups', []))


@operation
@with_neutron_client
def creation_validation(neutron_client, **kwargs):
    _sg_creation_validation(neutron_client, 'remote_ip_prefix')


def _egress_rules(rules):
    return [rule for rule in rules if rule.get('direction') == 'egress']


def _rules_for_sg_id(neutron_client, id):
    rules = neutron_client.list_security_group_rules()['security_group_rules']
    rules = [rule for rule in rules if rule['security_group_id'] == id]
    return rules


def process_rules(client, sgr_default_values, cidr_field_name,
                  remote_group_field_name, min_port_field_name,
                  max_port_field_name):
    rules_to_apply = ctx.node.properties['rules']
    security_group_rules = []
    for rule in rules_to_apply:
        security_group_rules.append(
            _process_rule(rule, client, sgr_default_values, cidr_field_name,
                          remote_group_field_name, min_port_field_name,
                          max_port_field_name))

    return security_group_rules


def _process_rule(rule, client, sgr_default_values, cidr_field_name,
                  remote_group_field_name, min_port_field_name,
                  max_port_field_name):
    ctx.logger.debug(
        "Security group rule before transformations: {0}".format(rule))

    sgr = copy.deepcopy(sgr_default_values)
    if 'port' in rule:
        rule[min_port_field_name] = rule['port']
        rule[max_port_field_name] = rule['port']
        del rule['port']
    sgr.update(rule)

    if (remote_group_field_name in sgr) and sgr[remote_group_field_name]:
        sgr[cidr_field_name] = None
    elif ('remote_group_node' in sgr) and sgr['remote_group_node']:
        _, remote_group_node = _capabilities_of_node_named(
            sgr['remote_group_node'])
        sgr[remote_group_field_name] = remote_group_node[OPENSTACK_ID_PROPERTY]
        del sgr['remote_group_node']
        sgr[cidr_field_name] = None
    elif ('remote_group_name' in sgr) and sgr['remote_group_name']:
        sgr[remote_group_field_name] = \
            client.get_id_from_resource(
                client.cosmo_get_named(
                    SECURITY_GROUP_OPENSTACK_TYPE, sgr['remote_group_name']))
        del sgr['remote_group_name']
        sgr[cidr_field_name] = None

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


def _sg_creation_validation(client, cidr_field_name, **kwargs):
    validate_resource(ctx, client, SECURITY_GROUP_OPENSTACK_TYPE)

    ctx.logger.debug('validating CIDR for rules with a {0} field'.format(
        cidr_field_name))
    for rule in ctx.node.properties['rules']:
        if cidr_field_name in rule:
            validate_ip_or_range_syntax(ctx, rule[cidr_field_name])
