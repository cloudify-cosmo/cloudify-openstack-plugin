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

import json
import copy
from functools import partial

from cloudify import ctx
from cloudify.decorators import operation
from openstack_plugin_common import (
    transform_resource_name,
    with_neutron_client,
    delete_resource_and_runtime_properties,
)
from openstack_plugin_common.security_group import (
    build_sg_data,
    process_rules,
    use_external_sg,
    set_sg_runtime_properties,
    delete_sg,
    raise_mismatching_descriptions_error,
    raise_mismatching_rules_error,
    test_sg_rules_equality,
    sg_creation_validation,
    RUNTIME_PROPERTIES_KEYS
)

# DEFAULT_EGRESS_RULES are based on
# https://github.com/openstack/neutron/blob/5385d06f86a1309176b5f688071e6ea55d91e8e5/neutron/db/securitygroups_db.py#L132-L136  # noqa
SUPPORTED_ETHER_TYPES = ('IPv4', 'IPv6')

DEFAULT_RULE_VALUES = {
    'direction': 'ingress',
    'ethertype': 'IPv4',
    'port_range_min': 1,
    'port_range_max': 65535,
    'protocol': 'tcp',
    'remote_group_id': None,
    'remote_ip_prefix': '0.0.0.0/0',
}

DEFAULT_EGRESS_RULES = []
for ethertype in SUPPORTED_ETHER_TYPES:
    DEFAULT_EGRESS_RULES.append({
        'direction': 'egress',
        'ethertype': ethertype,
        'port_range_max': None,
        'port_range_min': None,
        'protocol': None,
        'remote_group_id': None,
        'remote_ip_prefix': None,
    })


@operation
@with_neutron_client
def create(neutron_client, **kwargs):

    security_group = build_sg_data()

    sg_rules = process_rules(neutron_client, DEFAULT_RULE_VALUES,
                             'remote_ip_prefix', 'remote_group_id',
                             'port_range_min', 'port_range_max')

    disable_default_egress_rules = ctx.node.properties.get(
        'disable_default_egress_rules')

    # We do expect to see the default egress rules
    # if they shouldn't be disabled
    expected_sg_rules = sg_rules if disable_default_egress_rules \
        else sg_rules + DEFAULT_EGRESS_RULES

    existing_sg_equivalence_verifier = \
        partial(_existing_sg_equivalence_verifier,
                security_group=security_group,
                expected_sg_rules=expected_sg_rules)

    if use_external_sg(neutron_client, existing_sg_equivalence_verifier):
        return

    transform_resource_name(ctx, security_group)

    sg = neutron_client.create_security_group(
        {'security_group': security_group})['security_group']

    set_sg_runtime_properties(sg, neutron_client)

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
        delete_resource_and_runtime_properties(ctx, neutron_client,
                                               RUNTIME_PROPERTIES_KEYS)
        raise


@operation
@with_neutron_client
def delete(neutron_client, **kwargs):
    delete_sg(neutron_client)


@operation
@with_neutron_client
def creation_validation(neutron_client, **kwargs):
    sg_creation_validation(neutron_client, 'remote_ip_prefix')


def _egress_rules(rules):
    return [rule for rule in rules if rule.get('direction') == 'egress']


def _rules_for_sg_id(neutron_client, id):
    rules = neutron_client.list_security_group_rules()['security_group_rules']
    rules = [rule for rule in rules if rule['security_group_id'] == id]
    return rules


def _existing_sg_equivalence_verifier(existing_sg, security_group,
                                      expected_sg_rules):
    if existing_sg['description'] != security_group['description']:
        raise_mismatching_descriptions_error(security_group['name'])

    r1 = existing_sg['security_group_rules']
    r2 = expected_sg_rules

    # XXX: check later whether excluding tenant_id is OK in all cases.
    excluded_fields = ('id', 'security_group_id', 'tenant_id')

    def sg_rule_comparison_serializer(security_group_rule):
        r = copy.deepcopy(security_group_rule)
        for excluded_field in excluded_fields:
            if excluded_field in r:
                del r[excluded_field]
        return json.dumps(r, sort_keys=True)

    if not test_sg_rules_equality(r1, r2, sg_rule_comparison_serializer):
        raise_mismatching_rules_error(security_group['name'], r1, r2)
