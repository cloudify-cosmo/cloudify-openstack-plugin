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

from openstack_plugin_common import (with_nova_client,
                                     get_openstack_id,
                                     get_property,
                                     is_external_resource,
                                     use_external_resource,
                                     delete_resource_and_runtime_properties,
                                     delete_runtime_properties,
                                     create_object_dict,
                                     add_list_to_runtime_properties,
                                     set_openstack_runtime_properties,
                                     COMMON_RUNTIME_PROPERTIES_KEYS)

HOST_AGGREGATE_OPENSTACK_TYPE = 'aggregate'
HOSTS_PROPERTY = 'hosts'
METADATA_PROPERTY = 'metadata'
RUNTIME_PROPERTIES_KEYS = COMMON_RUNTIME_PROPERTIES_KEYS


def _add_hosts(ctx, nova_client, host_aggregate, hosts):
    for host in hosts:
        ctx.logger.debug(
            'Adding host {0} to aggregate {1}'
            .format(host, host_aggregate)
        )

        nova_client.aggregates.add_host(host_aggregate, host)

    if HOSTS_PROPERTY in ctx.instance.runtime_properties:
        hosts = list(
            set(hosts + ctx.instance.runtime_properties[HOSTS_PROPERTY])
        )

    ctx.instance.runtime_properties[HOSTS_PROPERTY] = hosts


def _set_metadata(ctx, nova_client, host_aggregate, kwargs):
    metadata = get_property(ctx, METADATA_PROPERTY, kwargs, {})

    if metadata:
        ctx.logger.debug(
            'Setting metadata {0} for aggregate {1}'
            .format(metadata, host_aggregate)
        )

        nova_client.aggregates.set_metadata(host_aggregate, metadata)


def _remove_hosts(ctx, nova_client, host_aggregate_id, hosts):
    for host in hosts:
        ctx.logger.debug(
            'Removing host {0} from aggregate {1}'
            .format(host, host_aggregate_id)
        )
        nova_client.aggregates.remove_host(host_aggregate_id, host)

    current_hosts = [
        host
        for host in ctx.instance.runtime_properties.get(HOSTS_PROPERTY, [])
        if host not in hosts
    ]

    if current_hosts:
        ctx.instance.runtime_properties[HOSTS_PROPERTY] = current_hosts
    else:
        delete_runtime_properties(ctx, HOSTS_PROPERTY)


@operation
@with_nova_client
def create(nova_client, args, **kwargs):
    if use_external_resource(ctx, nova_client, HOST_AGGREGATE_OPENSTACK_TYPE):
        return

    host_aggregate_dict = create_object_dict(
        ctx,
        HOST_AGGREGATE_OPENSTACK_TYPE,
        args
    )

    host_aggregate = nova_client.aggregates.create(**host_aggregate_dict)
    hosts = get_property(ctx, HOSTS_PROPERTY, args, [])
    _add_hosts(ctx, nova_client, host_aggregate, hosts)
    _set_metadata(ctx, nova_client, host_aggregate, args)

    set_openstack_runtime_properties(
        ctx,
        host_aggregate,
        HOST_AGGREGATE_OPENSTACK_TYPE
    )


@operation
@with_nova_client
def delete(nova_client, **kwargs):
    if not is_external_resource(ctx):
        host_aggregate = nova_client.aggregates.get(get_openstack_id(ctx))
        _remove_hosts(
            ctx,
            nova_client,
            get_openstack_id(ctx),
            host_aggregate.hosts
        )

        if HOSTS_PROPERTY in ctx.instance.runtime_properties:
            ctx.instance.runtime_properties.pop(HOSTS_PROPERTY, None)

    delete_resource_and_runtime_properties(
        ctx,
        nova_client,
        RUNTIME_PROPERTIES_KEYS
    )


@operation
@with_nova_client
def update(nova_client, args, **kwargs):
    if HOST_AGGREGATE_OPENSTACK_TYPE in args:
        host_aggregate = nova_client.aggregates.update(
            get_openstack_id(ctx),
            args.get(HOST_AGGREGATE_OPENSTACK_TYPE)
        )

        set_openstack_runtime_properties(
            ctx,
            host_aggregate,
            HOST_AGGREGATE_OPENSTACK_TYPE
        )

    _set_metadata(ctx, nova_client, get_openstack_id(ctx), args)


@operation
@with_nova_client
def list_host_aggregates(nova_client, **kwargs):
    host_aggregates_list = nova_client.aggregates.list()

    add_list_to_runtime_properties(
        ctx,
        HOST_AGGREGATE_OPENSTACK_TYPE,
        host_aggregates_list
    )


@operation
@with_nova_client
def add_hosts(nova_client, hosts, **kwargs):
    _add_hosts(ctx, nova_client, get_openstack_id(ctx), hosts)


@operation
@with_nova_client
def remove_hosts(nova_client, hosts, **kwargs):
    _remove_hosts(ctx, nova_client, get_openstack_id(ctx), hosts)
