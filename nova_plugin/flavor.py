#########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
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

from openstack_plugin_common import (
    with_nova_client,
    use_external_resource,
    delete_runtime_properties,
    delete_resource_and_runtime_properties,
    create_object_dict,
    add_list_to_runtime_properties,
    set_openstack_runtime_properties,
    COMMON_RUNTIME_PROPERTIES_KEYS
)

FLAVOR_OPENSTACK_TYPE = 'flavor'

EXTRA_SPECS_PROPERTY = 'extra_specs'

TENANTS_PROPERTY = 'tenants'

RUNTIME_PROPERTIES_KEYS = COMMON_RUNTIME_PROPERTIES_KEYS


def _set_extra_specs(ctx, flavor):
    extra_specs = ctx.node.properties.get(EXTRA_SPECS_PROPERTY, {})

    if extra_specs:
        ctx.logger.info(
            'Setting extra specs: {0} for flavor: {1}'
            .format(extra_specs, flavor.to_dict())
        )

        flavor.set_keys(extra_specs)

    ctx.instance.runtime_properties[EXTRA_SPECS_PROPERTY] = extra_specs


def _set_tenants_access(ctx, nova_client, flavor):
    tenants = ctx.node.properties.get(TENANTS_PROPERTY, [])

    for tenant in tenants:
        ctx.logger.info(
            'Adding tenant access: {0} for flavor: {1}'
            .format(tenant, flavor.to_dict())
        )
        nova_client.flavor_access.add_tenant_access(flavor, tenant)

    ctx.instance.runtime_properties[TENANTS_PROPERTY] = tenants


@operation(resumable=True)
@with_nova_client
def create(nova_client, args, **kwargs):
    if use_external_resource(ctx, nova_client, FLAVOR_OPENSTACK_TYPE):
        return

    flavor_dict = create_object_dict(ctx, FLAVOR_OPENSTACK_TYPE, args, {})
    ctx.logger.info('Creating flavor: {0}'.format(flavor_dict))

    flavor = nova_client.flavors.create(**flavor_dict)
    set_openstack_runtime_properties(ctx, flavor, FLAVOR_OPENSTACK_TYPE)

    _set_extra_specs(ctx, flavor)
    _set_tenants_access(ctx, nova_client, flavor)


@operation(resumable=True)
@with_nova_client
def delete(nova_client, **kwargs):
    delete_resource_and_runtime_properties(
        ctx,
        nova_client,
        RUNTIME_PROPERTIES_KEYS
    )

    delete_runtime_properties(ctx, [EXTRA_SPECS_PROPERTY, TENANTS_PROPERTY])


@operation(resumable=True)
@with_nova_client
def list_flavors(nova_client, args, **kwargs):
    flavor_list = nova_client.flavors.list(**args)
    add_list_to_runtime_properties(ctx, FLAVOR_OPENSTACK_TYPE, flavor_list)
