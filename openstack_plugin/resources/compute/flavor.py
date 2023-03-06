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
from openstack_sdk.resources.compute import OpenstackFlavor
from openstack_plugin.decorators import (with_openstack_resource,
                                         with_compat_node)
from openstack_plugin.constants import (RESOURCE_ID, FLAVOR_OPENSTACK_TYPE)
from openstack_plugin.utils import add_resource_list_to_runtime_properties


@with_compat_node
@with_openstack_resource(OpenstackFlavor)
def create(openstack_resource):
    """
    Create openstack flavor
    :param openstack_resource: Instance of openstack flavor resource
    """
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id
    extra_specs = ctx.node.properties.get('extra_specs', {})
    tenants = ctx.node.properties.get('tenants', [])
    if extra_specs:
        openstack_resource.set_flavor_specs(created_resource.id, extra_specs)
    if tenants:
        for tenant in tenants:
            openstack_resource.add_flavor_access(created_resource.id, tenant)


@with_compat_node
@with_openstack_resource(OpenstackFlavor)
def list_flavors(openstack_resource, query={}, details=True):
    """

    :param openstack_resource: Instance of openstack flavor resource
    :param kwargs query: Optional query parameters to be sent to limit
                                 the resources being returned.
    :param bool details: When set to ``False``
                :class:`~openstack.compute.v2.flavor.Flavor` instances
                will be returned. The default, ``True``, will cause
                :class:`~openstack.compute.v2.flavor.FlavorDetail`
                instances to be returned.
    """
    query['details'] = details
    flavors = openstack_resource.list(query=query)
    add_resource_list_to_runtime_properties(FLAVOR_OPENSTACK_TYPE, flavors)


@with_compat_node
@with_openstack_resource(OpenstackFlavor)
def delete(openstack_resource):
    """
    Delete flavor resource
    :param openstack_resource: Instance of openstack flavor resource.
    """
    openstack_resource.delete()


@with_compat_node
@with_openstack_resource(OpenstackFlavor)
def update(openstack_resource, args):
    """
    Update openstack flavor by passing args dict that contains the info that
    need to be updated
    :param openstack_resource: instance of openstack flavor resource
    :param args: dict of information need to be updated
    """
    # TODO This need to be uncomment whenever openstack allow for update
    #  operation since the following actions are only supported
    #  https://git.io/fh93b
    # args = reset_dict_empty_keys(args)
    # openstack_resource.update(args)
    raise NonRecoverableError(
        'Openstack SDK does not support flavor update operation')
