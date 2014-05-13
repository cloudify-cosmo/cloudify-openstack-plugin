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

import re
from cloudify.decorators import operation
from openstack_plugin_common import with_neutron_client

NODE_NAME_RE = re.compile('^(.*)_.*$')  # Anything before last underscore


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
                    raise RuntimeError(
                        "More than one node named '{0}' "
                        "in capabilities".format(node_name))
                result = (node_id, caps[node_id])
    if not result:
        raise RuntimeError(
            "Could not find node named '{0}' "
            "in capabilities".format(node_name))
    return result


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

    rules_to_apply = ctx.properties['rules']
    egress_rules_to_apply = _egress_rules(rules_to_apply)

    if 'disable_egress' in ctx.properties:
        if egress_rules_to_apply and ctx.properties['disable_egress']:
            raise RuntimeError(
                "Security group {0} can not have both "
                "disable_egress and an egress rule".format(
                    security_group['name']))
        do_disable_egress = True
    else:
        do_disable_egress = False

    sg = None
    ls = list(neutron_client.cosmo_list('security_group',
                                        name=security_group['name']))
    if len(ls) > 1:
        raise RuntimeError("Can not use security group '{0}' because more"
                           "than one such group exists".format(
                               security_group['name']))

    if len(ls) == 1:
        sg = ls[0]
        ctx.logger.info("Using existing security group '{0}'".format(
                        security_group['name']))
        ctx['external_id'] = sg['id']
        return

    if not ctx.properties.get('create_if_missing', True):
        raise RuntimeError("Security group '{0}' does not exist "
                           "and create_if_missing is false".format(
                               security_group['name']))
    ctx.logger.info("Creating security group '{0}'".format(
                    security_group['name']))
    sg = neutron_client.create_security_group(
        {'security_group': security_group})['security_group']

    if egress_rules_to_apply or do_disable_egress:
        for er in _egress_rules(_rules_for_sg_id(neutron_client, sg['id'])):
            neutron_client.delete_security_group_rule(er['id'])

    for rule in rules_to_apply:
        ctx.logger.debug(
            "security_group.create() rule before transformations: {0}".format(
                rule))
        sgr = {
            'direction': 'ingress',
            'port_range_max': rule.get('port', 65535),
            'port_range_min': rule.get('port', 1),
            'protocol': 'tcp',
            'remote_group_id': None,
            'remote_ip_prefix': None,
            'security_group_id': sg['id'],
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
        neutron_client.create_security_group_rule({'security_group_rule': sgr})

    ctx['external_id'] = sg['id']


@operation
@with_neutron_client
def delete(ctx, neutron_client, **kwargs):
    neutron_client.delete_security_group(ctx.runtime_properties['external_id'])
