# #######
# Copyright (c) 2019 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Third party imports
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError

# Local imports
from openstack_sdk.resources.compute import OpenstackHostAggregate
from openstack_plugin.decorators import (with_openstack_resource,
                                         with_compat_node)
from openstack_plugin.constants import (RESOURCE_ID,
                                        HOST_AGGREGATE_OPENSTACK_TYPE)
from openstack_plugin.utils import add_resource_list_to_runtime_properties


def _add_hosts(openstack_resource, hosts):
    """
    This method is to add list of hosts to the aggregate openstack instance
    :param openstack_resource: Instance of openstack host aggregate resource
    :param hosts: List of hosts (strings) that should be added to the aggregate
    """
    if isinstance(hosts, list):
        for host in hosts:
            # Add host to the target host aggregate
            openstack_resource.add_host(host)
    else:
        raise NonRecoverableError(
            'invalid data type {0} for hosts'.format(type(hosts)))

    # Update/Add hosts as runtime properties for the current instance
    if 'hosts' in ctx.instance.runtime_properties:
        hosts = list(set(hosts + ctx.instance.runtime_properties['hosts']))

    ctx.instance.runtime_properties['hosts'] = hosts


def _remove_hosts(openstack_resource, hosts, update_on_remove=False):
    """
    This method is to remove list of hosts from aggregate openstack instance
    :param openstack_resource: Instance of openstack host aggregate resource
    :param hosts: List of hosts (strings) that should be remove form aggregate
    """
    if isinstance(hosts, list):
        updated_hosts = [host for host in hosts]
        for host in hosts:
            # remove host from the target host aggregate
            openstack_resource.remove_host(host)
            if update_on_remove:
                updated_hosts.remove(host)
                ctx.instance.runtime_properties['hosts'] = updated_hosts
                # save current state before remove next host
                ctx.instance.update()
    else:
        raise NonRecoverableError(
            'invalid data type {0} for hosts'.format(type(hosts)))

    # Get the current remaining hosts in order to update the hosts as a
    # result of that
    current_hosts = [
        host
        for host in ctx.instance.runtime_properties.get('hosts', [])
        if host not in hosts
    ]

    # Update the current hosts as they should represent the remaining hosts
    # that should be part of the `hosts` runtime property
    if current_hosts:
        ctx.instance.runtime_properties['hosts'] = current_hosts
    else:
        del ctx.instance.runtime_properties['hosts']


@with_compat_node
@with_openstack_resource(OpenstackHostAggregate)
def create(openstack_resource):
    """
    Create openstack host aggregate instance
    :param openstack_resource: Instance of openstack host aggregate resource
    """
    # First create host aggregate instance using the configuration provided
    # by users when create cloudify node
    created_resource = openstack_resource.create()

    # Set the "id" as a runtime property for the created host aggregate
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_compat_node
@with_openstack_resource(OpenstackHostAggregate)
def configure(openstack_resource):
    """
    Configure host aggregate by adding metadata with created host aggregate
    :param openstack_resource: Instance of openstack host aggregate resource
    """

    # Check to see if metadata is provided or not so that we can attach them
    # to created host aggregate
    if ctx.node.properties.get('metadata'):
        # Metadata values should be in strong format
        for key, value in ctx.node.properties['metadata'].iteritems():
            if not isinstance(value, basestring):
                ctx.node.properties['metadata'][key] = unicode(value)
        openstack_resource.set_metadata(ctx.node.properties['metadata'])

    # Check to see if there hosts is provided or not so that we can add
    # hosts and attach them to the aggregate created
    if ctx.node.properties.get('hosts'):
        _add_hosts(openstack_resource, ctx.node.properties['hosts'])


@with_compat_node
@with_openstack_resource(OpenstackHostAggregate)
def update(openstack_resource, args):
    """
    Update openstack host aggregate by passing args dict that contains
    the info that need to be updated
    :param openstack_resource: Instance of openstack host aggregate resource
    :param dict args: dict of information need to be updated
    """
    # TODO This need to be uncomment whenever openstack allow for update
    #  operation since the following actions are only supported
    #  https://git.io/fhSFH
    # args = reset_dict_empty_keys(args)
    # openstack_resource.update(args)
    raise NonRecoverableError(
        'Openstack SDK does not support host aggregate  update operation')


@with_compat_node
@with_openstack_resource(OpenstackHostAggregate)
def list_aggregates(openstack_resource):
    """
    List openstack host aggregate
    :param openstack_resource: Instance of openstack host aggregate resource.
    """
    aggregates = openstack_resource.list()
    add_resource_list_to_runtime_properties(HOST_AGGREGATE_OPENSTACK_TYPE,
                                            aggregates)


@with_compat_node
@with_openstack_resource(OpenstackHostAggregate)
def delete(openstack_resource):
    """
    Delete host aggregate resource
    :param openstack_resource: Instance of openstack host aggregate resource.
    """
    # Before delete the aggregate, check to see if there are hosts attached
    # to the aggregates first, checking runtime properties because use could
    # run "cloudify.interfaces.operations.remove_hosts" operation before
    # run uninstall which helps to avoid run delete host multiple times
    if ctx.instance.runtime_properties.get('hosts'):
        _remove_hosts(openstack_resource,
                      ctx.instance.runtime_properties['hosts'],
                      update_on_remove=True)
    openstack_resource.delete()


@with_compat_node
@with_openstack_resource(OpenstackHostAggregate)
def add_hosts(openstack_resource, hosts):
    """
    Add hosts to an aggregate
    :param openstack_resource: Instance of openstack host aggregate resource.
    :param list hosts: List of host strings that should be added to the host
    aggregate resource
    """
    _add_hosts(openstack_resource, hosts)


@with_compat_node
@with_openstack_resource(OpenstackHostAggregate)
def remove_hosts(openstack_resource, hosts):
    """
    Remove hosts from an aggregate
    :param openstack_resource: Instance of openstack host aggregate resource.
    :param list hosts: List of host strings that should be removed from host
    aggregate resource
    """
    _remove_hosts(openstack_resource, hosts)
