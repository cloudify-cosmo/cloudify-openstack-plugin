#########
# Copyright (c) 2018 GigaSpaces Technologies Ltd. All rights reserved
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
    use_external_resource,
    create_object_dict,
    add_list_to_runtime_properties,
    set_neutron_runtime_properties,
    get_relationships_by_relationship_type,
    delete_resource_and_runtime_properties,
    COMMON_RUNTIME_PROPERTIES_KEYS,
    OPENSTACK_ID_PROPERTY,
    OPENSTACK_TYPE_PROPERTY,
    with_resume_operation
)

RBAC_POLICY_OPENSTACK_TYPE = 'rbac_policy'
RBAC_POLICY_APPLIED_FOR_RELATIONSHIP_TYPE = \
    'cloudify.openstack.rbac_policy_applied_to'


def find_resource_to_apply_rbac_policy(ctx):
    found_relationships = get_relationships_by_relationship_type(
        ctx,
        RBAC_POLICY_APPLIED_FOR_RELATIONSHIP_TYPE
    )

    if len(found_relationships) == 0:
        ctx.logger.info(
            'Resource for which RBAC policy may be applied '
            'not found using {} relationship'
            .format(RBAC_POLICY_APPLIED_FOR_RELATIONSHIP_TYPE)
        )

        return {}

    if len(found_relationships) > 1:
        raise NonRecoverableError(
            'Multiple ({0}) resources for which RBAC policy may be applied '
            'found using relationship {1}'
            .format(
                len(found_relationships),
                RBAC_POLICY_APPLIED_FOR_RELATIONSHIP_TYPE
            )
        )

    found_resource = found_relationships[0].target.instance
    ctx.logger.info(
        '{0} resource for which RBAC policy may be applied '
        'found using {1} relationship)'
        .format(found_resource, RBAC_POLICY_APPLIED_FOR_RELATIONSHIP_TYPE)
    )

    id = found_resource.runtime_properties.get(OPENSTACK_ID_PROPERTY, None)
    type = found_resource.runtime_properties.get(
        OPENSTACK_TYPE_PROPERTY,
        None
    )

    if not id or not type:
        ctx.logger.warn(
            'Found using relationship resource has not defined either '
            '"id" or "type" runtime_property. Skipping.'
        )

        return {}

    return {
        'object_type': type,
        'object_id': id
    }


def validate_found_resource(input_dict, found_resource):
    if found_resource:
        for key in found_resource:
            if key in input_dict and input_dict.get(key):
                raise NonRecoverableError(
                    'Multiple definitions of resource for which '
                    'RBAC policy should be applied. '
                    'You specified it both using properties / operation '
                    'inputs and relationship.'
                )


def create_rbac_policy_object_dict(ctx, args):
    found_resource = find_resource_to_apply_rbac_policy(ctx)
    validate_found_resource(
        ctx.node.properties.get(RBAC_POLICY_OPENSTACK_TYPE, {}),
        found_resource
    )

    validate_found_resource(
        args.get(RBAC_POLICY_OPENSTACK_TYPE, {}),
        found_resource
    )

    rbac_policy = create_object_dict(
        ctx,
        RBAC_POLICY_OPENSTACK_TYPE,
        args,
        found_resource
    )

    return rbac_policy


@operation(resumable=True)
@with_resume_operation
@with_neutron_client
def create(neutron_client, args, **kwargs):
    if use_external_resource(ctx, neutron_client, RBAC_POLICY_OPENSTACK_TYPE):
        return

    rbac_policy_raw = create_rbac_policy_object_dict(ctx, args)
    ctx.logger.info('rbac_policy: {0}'.format(rbac_policy_raw))

    rbac_policy = rbac_policy_raw.copy()
    rbac_policy.pop('name', None)  # rbac_policy doesn't accept name parameter

    rp = neutron_client.create_rbac_policy({
        RBAC_POLICY_OPENSTACK_TYPE: rbac_policy
    })[RBAC_POLICY_OPENSTACK_TYPE]
    rp['name'] = None

    set_neutron_runtime_properties(ctx, rp, RBAC_POLICY_OPENSTACK_TYPE)


@operation(resumable=True)
@with_resume_operation
@with_neutron_client
def delete(neutron_client, **kwargs):
    delete_resource_and_runtime_properties(
        ctx,
        neutron_client,
        COMMON_RUNTIME_PROPERTIES_KEYS
    )


@operation(resumable=True)
@with_resume_operation
@with_neutron_client
def list_rbac_policies(neutron_client, args, **kwargs):
    rbac_policies = neutron_client.list_rbac_policies(**args)
    add_list_to_runtime_properties(
        ctx,
        RBAC_POLICY_OPENSTACK_TYPE,
        rbac_policies.get('rbac_policies', [])
    )


@operation(resumable=True)
@with_resume_operation
@with_neutron_client
def find_and_delete(neutron_client, args, **kwargs):
    reference_rbac_policy = create_rbac_policy_object_dict(ctx, args)
    reference_rbac_policy.pop('name', None)
    rbac_policies_list = neutron_client.list_rbac_policies() \
        .get('rbac_policies', [])

    for rbac_policy in rbac_policies_list:
        if all(
            item in rbac_policy.items()
            for item
            in reference_rbac_policy.items()
        ):
            id = rbac_policy['id']
            ctx.logger.info(
                'Found RBAC policy with ID: {0} - deleting ...'.format(id)
            )

            neutron_client.cosmo_delete_resource(
                RBAC_POLICY_OPENSTACK_TYPE,
                id
            )

            return

    ctx.logger.warn('No suitable RBAC policy found')
