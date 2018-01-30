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

from openstack_plugin_common import (with_keystone_client,
                                     use_external_resource,
                                     delete_resource_and_runtime_properties,
                                     validate_resource,
                                     create_object_dict,
                                     get_openstack_id,
                                     add_list_to_runtime_properties,
                                     set_openstack_runtime_properties,
                                     COMMON_RUNTIME_PROPERTIES_KEYS)

USER_OPENSTACK_TYPE = 'user'

RUNTIME_PROPERTIES_KEYS = COMMON_RUNTIME_PROPERTIES_KEYS


@operation
@with_keystone_client
def create(keystone_client, args, **kwargs):
    if use_external_resource(ctx, keystone_client, USER_OPENSTACK_TYPE):
        return

    user_dict = create_object_dict(ctx, USER_OPENSTACK_TYPE, args)
    user = keystone_client.users.create(**user_dict)

    set_openstack_runtime_properties(ctx, user, USER_OPENSTACK_TYPE)


@operation
@with_keystone_client
def delete(keystone_client, **kwargs):
    delete_resource_and_runtime_properties(ctx, keystone_client,
                                           RUNTIME_PROPERTIES_KEYS)


@operation
@with_keystone_client
def update(keystone_client, args, **kwargs):
    user_dict = create_object_dict(ctx, USER_OPENSTACK_TYPE, args)
    user_dict[USER_OPENSTACK_TYPE] = get_openstack_id(ctx)
    user = keystone_client.users.update(**user_dict)
    set_openstack_runtime_properties(ctx, user, USER_OPENSTACK_TYPE)


@with_keystone_client
def list_users(keystone_client, args, **kwargs):
    users_list = keystone_client.users.list(**args)
    users_list = users_list.get('users')
    add_list_to_runtime_properties(ctx, USER_OPENSTACK_TYPE, users_list)
