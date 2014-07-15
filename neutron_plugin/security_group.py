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
import re

import neutronclient.common.exceptions as neutron_exceptions

from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from openstack_plugin_common import (
    transform_resource_name,
    with_neutron_client,
)

NODE_NAME_RE = re.compile('^(.*)_.*$')  # Anything before last underscore

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


class RulesMismatchError(NonRecoverableError):
    pass


def _egress_rules(rules):
    return [rule for rule in rules if rule.get('direction') == 'egress']


def _rules_for_sg_id(neutron_client, id):
    rules = neutron_client.list_security_group_rules()['security_group_rules']
    rules = [rule for rule in rules if rule['security_group_id'] == id]
    return rules


def _capabilities_of_node_named(node_name, ctx):
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


def _find_existing_sg(ctx, neutron_client, security_group):
    existing_sgs = neutron_client.cosmo_list(
        'security_group',
        name=security_group['name']
    )
    existing_sgs = list(existing_sgs)
    if len(existing_sgs) > 1:
        raise NonRecoverableError("Multiple security groups with name '{0}' "
                                  "already exist while trying to create "
                                  "security group with same name".format(
                                      security_group['name']))
    if existing_sgs:
        ctx.logger.info("Found existing security group "
                        "with name '{0}'".format(security_group['name']))
        return existing_sgs[0]

    return None


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


@operation
@with_neutron_client
def create(ctx, neutron_client, **kwargs):
    """ Create security group with rules.
    Parameters transformations:
        rules.N.remote_group_name -> rules.N.remote_group_id
        rules.N.remote_group_node -> rules.N.remote_group_id
        (Node name in YAML)
    """

    security_group = {
        'description': None,
        'name': ctx.node_id,
    }

    security_group.update(ctx.properties['security_group'])
    transform_resource_name(security_group, ctx)

    existing_sg = _find_existing_sg(ctx, neutron_client, security_group)
    if existing_sg:
        if existing_sg['description'] != security_group['description']:
            raise NonRecoverableError("Descriptions of existing security group"
                                      " and the security group to be created "
                                      "do not match while the names do match."
                                      " Security group name: {0}".format(
                                          security_group['name']))

    rules_to_apply = ctx.properties['rules']
    egress_rules_to_apply = _egress_rules(rules_to_apply)

    do_disable_egress = ctx.properties.get('disable_egress')
    if do_disable_egress:
        if egress_rules_to_apply and ctx.properties['disable_egress']:
            raise NonRecoverableError(
                "Security group {0} can not have both "
                "disable_egress and an egress rule".format(
                    security_group['name']))

    security_group_rules = []
    for rule in rules_to_apply:
        ctx.logger.debug(
            "security_group.create() rule before transformations: {0}".format(
                rule))
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
                sgr['remote_group_node'], ctx)
            sgr['remote_group_id'] = remote_group_node['external_id']
            del sgr['remote_group_node']

        if ('remote_group_name' in sgr) and sgr['remote_group_name']:
            sgr['remote_group_id'] = neutron_client.cosmo_get_named(
                'security_group', sgr['remote_group_name'])['id']
            del sgr['remote_group_name']

        ctx.logger.debug(
            "security_group.create() rule after transformations: {0}".format(
                sgr))
        security_group_rules.append(sgr)

    if existing_sg:
        r1 = existing_sg['security_group_rules']
        r2 = security_group_rules
        if not (egress_rules_to_apply or do_disable_egress):
            # We do expect to see the default egress rules
            # if we don't have our own and we do not disable
            # the default egress rules.
            r2 = r2 + DEFAULT_EGRESS_RULES
        if _sg_rules_are_equal(r1, r2):
            ctx.logger.info("Using existing security group named '{0}' with "
                            "id {1}".format(
                                security_group['name'],
                                existing_sg['id']))
            ctx.runtime_properties['external_id'] = existing_sg['id']
            return
        else:
            raise RulesMismatchError("Rules of existing security group"
                                     " and the security group to be created "
                                     "or used do not match while the names "
                                     "do match. Security group name: '{0}'. "
                                     "Existing rules: {1}. "
                                     "Requested/expected rules: {2} "
                                     "".format(
                                         security_group['name'],
                                         r1,
                                         r2))

    sg = neutron_client.create_security_group(
        {'security_group': security_group})['security_group']

    if egress_rules_to_apply or do_disable_egress:
        for er in _egress_rules(_rules_for_sg_id(neutron_client, sg['id'])):
            neutron_client.delete_security_group_rule(er['id'])

    for sgr in security_group_rules:
        sgr['security_group_id'] = sg['id']
        neutron_client.create_security_group_rule({'security_group_rule': sgr})
    ctx.runtime_properties['external_id'] = sg['id']


@operation
@with_neutron_client
def delete(ctx, neutron_client, **kwargs):
    sg_id = ctx.runtime_properties['external_id']
    try:
        neutron_client.delete_security_group(sg_id)
    except neutron_exceptions.NeutronClientException, e:
        if not hasattr(e, 'status_code'):
            raise NonRecoverableError("Neutron client error: " + str(e))

        # Sample sequence of events that explains the handling of 404 error as
        # implemented in the code below (just warning):
        # * We had a server that uses this security group.
        # * We deleted the server
        # * Other deployment deleted the security group
        # * We are trying to delete the security group
        if e.status_code == 404:
            ctx.logger.warn("Security group with id '{0}' not found "
                            "while trying to delete it.".format(sg_id))
            return
        # The security group might be used by other deployments
        # so just warning.
        if e.status_code == 409:
            ctx.logger.warn("Security group with id '{0}' is in use "
                            "while trying to delete it.".format(sg_id))
            return
        raise NonRecoverableError("Neutron client error: " + str(e))
