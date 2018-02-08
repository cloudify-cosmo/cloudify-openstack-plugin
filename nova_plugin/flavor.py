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

from openstack_plugin_common import (with_nova_client,
                                     use_external_resource,
                                     delete_resource_and_runtime_properties,
                                     create_object_dict,
                                     add_list_to_runtime_properties,
                                     set_openstack_runtime_properties,
                                     COMMON_RUNTIME_PROPERTIES_KEYS)

FLAVOR_OPENSTACK_TYPE = 'flavor'

RUNTIME_PROPERTIES_KEYS = COMMON_RUNTIME_PROPERTIES_KEYS


@operation
@with_nova_client
def create(nova_client, args, **kwargs):
    if use_external_resource(ctx, nova_client, FLAVOR_OPENSTACK_TYPE):
        return

    flavor_dict = create_object_dict(ctx, FLAVOR_OPENSTACK_TYPE, args)
    flavor = nova_client.flavors.create(**flavor_dict)
    set_openstack_runtime_properties(ctx, flavor, FLAVOR_OPENSTACK_TYPE)


@operation
@with_nova_client
def delete(nova_client, **kwargs):
    delete_resource_and_runtime_properties(ctx, nova_client,
                                           RUNTIME_PROPERTIES_KEYS)


@with_nova_client
def list_flavors(nova_client, args, **kwargs):
    flavor_list = nova_client.flavors.list(**args)
    add_list_to_runtime_properties(ctx, FLAVOR_OPENSTACK_TYPE, flavor_list)
