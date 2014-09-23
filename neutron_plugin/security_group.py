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
import json

import neutronclient.common.exceptions as neutron_exceptions

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from openstack_plugin_common import (
    transform_resource_name,
    with_neutron_client,
    get_resource_id,
    use_external_resource,
    delete_resource_and_runtime_properties,
    delete_runtime_properties,
    OPENSTACK_ID_PROPERTY,
    OPENSTACK_TYPE_PROPERTY,
    OPENSTACK_NAME_PROPERTY,
    COMMON_RUNTIME_PROPERTIES_KEYS
)

# DEFAULT_EGRESS_RULES are based on
# https://github.com/openstack/neutron/blob/5385d06f86a1309176b5f688071e6ea55d91e8e5/neutron/db/securitygroups_db.py#L132-L136  # noqa
SUPPORTED_ETHER_TYPES = ('IPv4', 'IPv6')
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

SECURITY_GROUP_OPENSTACK_TYPE = 'security_group'

# Runtime properties
RUNTIME_PROPERTIES_KEYS = COMMON_RUNTIME_PROPERTIES_KEYS


@operation
@with_neutron_client
def create(neutron_client, **kwargs):
    """ Create security group with rules.
    Parameters transformations:
        rules.N.remote_group_name -> rules.N.remote_group_id
        rules.N.remote_group_node -> rules.N.remote_group_id
        (Node name in YAML)
    """

    security_group = {
        'description': None,
        'name': get_resource_id(ctx, SECURITY_GROUP_OPENSTACK_TYPE),
    }

    security_group.update(ctx.properties['security_group'])

    rules_to_apply = ctx.properties['rules']
    from neutron_plugin.security_group_rule import _process_rule
    security_group_rules = []
    for rule in rules_to_apply:
        security_group_rules.append(_process_rule(rule, neutron_client))

    disable_default_egress_rules = ctx.properties.get(
        'disable_default_egress_rules')

    external_sg = use_external_resource(ctx, neutron_client,
                                        SECURITY_GROUP_OPENSTACK_TYPE)
    if external_sg:
        try:
            _ensure_existing_sg_is_identical(
                external_sg, security_group, security_group_rules,
                not disable_default_egress_rules)
            return
        except Exception:
            delete_runtime_properties(ctx, RUNTIME_PROPERTIES_KEYS)
            raise

    transform_resource_name(ctx, security_group)

    sg = neutron_client.create_security_group(
        {'security_group': security_group})['security_group']

    ctx.runtime_properties[OPENSTACK_ID_PROPERTY] = sg['id']
    ctx.runtime_properties[OPENSTACK_TYPE_PROPERTY] = \
        SECURITY_GROUP_OPENSTACK_TYPE
    ctx.runtime_properties[OPENSTACK_NAME_PROPERTY] = sg['name']

    try:
        if disable_default_egress_rules:
            for er in _egress_rules(_rules_for_sg_id(neutron_client,
                                                     sg['id'])):
                neutron_client.delete_security_group_rule(er['id'])

        for sgr in security_group_rules:
            sgr['security_group_id'] = sg['id']
            neutron_client.create_security_group_rule(
                {'security_group_rule': sgr})
    except neutron_exceptions.NeutronClientException:
        delete_resource_and_runtime_properties(ctx, neutron_client,
                                               RUNTIME_PROPERTIES_KEYS)
        raise


@operation
@with_neutron_client
def delete(neutron_client, **kwargs):
    delete_resource_and_runtime_properties(ctx, neutron_client,
                                           RUNTIME_PROPERTIES_KEYS)


def _ensure_existing_sg_is_identical(existing_sg, security_group,
                                     security_group_rules,
                                     expect_default_egress_rules):
    def _serialize_sg_rule_for_comparison(security_group_rule):
        r = copy.deepcopy(security_group_rule)
        # XXX: check later whether excluding tenant_id is OK in all cases.
        for excluded_field in ('id', 'security_group_id', 'tenant_id'):
            if excluded_field in r:
                del r[excluded_field]
        return json.dumps(r, sort_keys=True)

    def _sg_rules_are_equal(r1, r2):
        s1 = map(_serialize_sg_rule_for_comparison, r1)
        s2 = map(_serialize_sg_rule_for_comparison, r2)
        return set(s1) == set(s2)

    if existing_sg['description'] != security_group['description']:
        raise NonRecoverableError(
            "Descriptions of existing security group and the security group "
            "to be created do not match while the names do match. Security "
            "group name: {0}".format(security_group['name']))

    r1 = existing_sg['security_group_rules']
    r2 = security_group_rules
    if expect_default_egress_rules:
        # We do expect to see the default egress rules
        # if we don't have our own and we do not disable
        # the default egress rules.
        r2 = r2 + DEFAULT_EGRESS_RULES
    if not _sg_rules_are_equal(r1, r2):
        raise NonRecoverableError(
            "Rules of existing security group and the security group to be "
            "created or used do not match while the names do match. Security "
            "group name: '{0}'. Existing rules: {1}. Requested/expected rules:"
            " {2} ".format(security_group['name'], r1, r2))


def _egress_rules(rules):
    return [rule for rule in rules if rule.get('direction') == 'egress']


def _rules_for_sg_id(neutron_client, id):
    rules = neutron_client.list_security_group_rules()['security_group_rules']
    rules = [rule for rule in rules if rule['security_group_id'] == id]
    return rules
