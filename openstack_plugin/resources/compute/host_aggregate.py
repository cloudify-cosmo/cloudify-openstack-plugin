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
from openstack_plugin.decorators import with_openstack_resource
from openstack_plugin.constants import (RESOURCE_ID,
                                        HOST_AGGREGATE_OPENSTACK_TYPE)
from openstack_plugin.utils import add_resource_list_to_runtime_properties


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


@with_openstack_resource(OpenstackHostAggregate)
def set_metadata(openstack_resource):
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


@with_openstack_resource(OpenstackHostAggregate)
def list_aggregates(openstack_resource):
    """
    List openstack host aggregate
    :param openstack_resource: Instance of openstack host aggregate resource.
    """
    aggregates = openstack_resource.list()
    add_resource_list_to_runtime_properties(HOST_AGGREGATE_OPENSTACK_TYPE,
                                            aggregates)


@with_openstack_resource(OpenstackHostAggregate)
def delete(openstack_resource):
    """
    Delete host aggregate resource
    :param openstack_resource: Instance of openstack host aggregate resource.
    """
    openstack_resource.delete()


@with_openstack_resource(OpenstackHostAggregate)
def add_hosts(openstack_resource, hosts):
    """
    Add hosts to an aggregate
    :param openstack_resource: Instance of openstack host aggregate resource.
    :param list hosts: List of host strings that should be added to the host
    aggregate resource
    """
    if isinstance(hosts, list):
        for host in hosts:
            # Add host to the target host aggregate
            openstack_resource.add_host(host)
    else:
        raise NonRecoverableError(
            'invalid data type {0} for hosts'.format(type(hosts)))


@with_openstack_resource(OpenstackHostAggregate)
def remove_hosts(openstack_resource, hosts):
    """
    Remove hosts from an aggregate
    :param openstack_resource: Instance of openstack host aggregate resource.
    :param list hosts: List of host strings that should be removed from host
    aggregate resource
    """
    if isinstance(hosts, list):
        for host in hosts:
            # Add host to the target host aggregate
            openstack_resource.remove_host(host)
    else:
        raise NonRecoverableError(
            'invalid data type {0} for hosts'.format(type(hosts)))
