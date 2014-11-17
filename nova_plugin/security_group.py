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
    with_nova_client,
    delete_resource_and_runtime_properties
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


@operation
@with_nova_client
def create(nova_client, **kwargs):

    # default security group description is an empty string
    security_group = build_sg_data('')

    sgr_default_values = {
        'ip_protocol': 'tcp',
        'from_port': 1,
        'to_port': 65535,
        'cidr': '0.0.0.0/0',
        # 'group_id': None,
        # 'parent_group_id': None,
    }
    sg_rules = process_rules(nova_client, sgr_default_values,
                             'cidr', 'group_id', 'from_port', 'to_port')

    existing_sg_equivalence_verifier = \
        partial(_existing_sg_equivalence_verifier,
                security_group=security_group,
                sg_rules=sg_rules)

    if use_external_sg(nova_client, existing_sg_equivalence_verifier):
        return

    transform_resource_name(ctx, security_group)

    sg = nova_client.security_groups.create(
        security_group['name'], security_group['description'])

    set_sg_runtime_properties(sg, nova_client)

    try:
        for sgr in sg_rules:
            sgr['parent_group_id'] = sg.id
            nova_client.security_group_rules.create(**sgr)
    except Exception:
        delete_resource_and_runtime_properties(ctx, nova_client,
                                               RUNTIME_PROPERTIES_KEYS)
        raise


@operation
@with_nova_client
def delete(nova_client, **kwargs):
    delete_sg(nova_client)


@operation
@with_nova_client
def creation_validation(nova_client, **kwargs):
    sg_creation_validation(nova_client, 'cidr')


def _existing_sg_equivalence_verifier(existing_sg, security_group, sg_rules):
    if existing_sg.description != security_group['description']:
        raise_mismatching_descriptions_error(security_group['name'])

    r1 = existing_sg.rules
    r2 = sg_rules
    # TODO: also compare 'group_id' - will require making calls to nova to
    # get ids of remote groups, as existing rules only hold remote group
    #  name under 'group'
    excluded_fields = ('id', 'parent_group_id', 'group', 'group_id')

    def sg_rule_comparison_serializer(security_group_rule):
        r = copy.deepcopy(security_group_rule)
        for excluded_field in excluded_fields:
            if excluded_field in r:
                del r[excluded_field]
        if 'ip_range' in r:
            r['cidr'] = r['ip_range'].get('cidr')
            del(r['ip_range'])
        return json.dumps(r, sort_keys=True)

    if not test_sg_rules_equality(r1, r2, sg_rule_comparison_serializer):
        raise_mismatching_rules_error(security_group['name'], r1, r2)
