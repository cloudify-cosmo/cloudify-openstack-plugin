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

# Local imports
from openstack_sdk.resources.networks import OpenstackSecurityGroup
from openstack_sdk.resources.networks import OpenstackSecurityGroupRule

from openstack_plugin.decorators import (with_openstack_resource,
                                         with_compat_node)

from openstack_plugin.constants import (RESOURCE_ID,
                                        SECURITY_GROUP_OPENSTACK_TYPE)
from openstack_plugin.utils import (reset_dict_empty_keys,
                                    validate_resource_quota,
                                    add_resource_list_to_runtime_properties,
                                    validate_ip_or_range_syntax)


def security_group_creation_validation(openstack_resource):
    """
    This method will do validations for security groups related to quota
    resources and to validate ip range syntax for rules
    :param openstack_resource: instance of openstack security group resource
    """
    # Validate quota
    validate_resource_quota(openstack_resource, SECURITY_GROUP_OPENSTACK_TYPE)

    ctx.logger.debug('validating CIDR for rules with a remote_ip_prefix field')
    for rule in ctx.node.properties.get('security_group_rules', []):
        if 'remote_ip_prefix' in rule:
            validate_ip_or_range_syntax(ctx, rule['remote_ip_prefix'])


@with_compat_node
@with_openstack_resource(OpenstackSecurityGroup)
def create(openstack_resource):
    """
    Create openstack security group instance
    :param openstack_resource: instance of openstack security group resource
    """
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_compat_node
@with_openstack_resource(OpenstackSecurityGroup)
def configure(openstack_resource, security_group_rules=None):
    """
    This task will allow to add security group rules and attach them to
    created security group if they provided on the node configuration
    :param openstack_resource: security group instance
    :param security_group_rules: List of security group rules
    """
    client_config = ctx.node.properties.get('client_config')
    security_group_id = openstack_resource.resource_id

    # Define security group rule instance
    security_group_rule = \
        OpenstackSecurityGroupRule(client_config=client_config,
                                   logger=ctx.logger)

    # Check if the "disable_default_egress_rules" is enabled or not so that
    # we can remove default egress rules for current security group
    if ctx.node.properties.get('disable_default_egress_rules'):
        for sg_rule in security_group_rule.list(
                query={'security_group_id': security_group_id}):

            security_group_rule.resource_id = sg_rule.id
            security_group_rule.delete()

    security_group_rule.resource_id = None
    # Check the existing rules attached to current security groups
    # in order to apply them to that group
    for rule_config in security_group_rules:
        # Check if the config contains the security group id or not
        if not rule_config.get('security_group_id'):
            rule_config['security_group_id'] = security_group_id

        # Create new instance for each security group id
        security_group_rule.config = rule_config
        # Create security group rule
        security_group_rule.create()


@with_compat_node
@with_openstack_resource(OpenstackSecurityGroup)
def delete(openstack_resource):
    """
    Delete current openstack security group instance
    :param openstack_resource: instance of openstack security group  resource
    """
    if not ctx.instance.runtime_properties.get(RESOURCE_ID):
        ctx.logger.info('SecurityGroup is already uninitialized.')
        return
    openstack_resource.delete()


@with_compat_node
@with_openstack_resource(OpenstackSecurityGroup)
def update(openstack_resource, args):
    """
    Update openstack security group by passing args dict that contains
    the info that need to be updated
    :param openstack_resource: instance of openstack security group resource
    :param args: dict of information need to be updated
    """
    args = reset_dict_empty_keys(args)
    openstack_resource.update(args)


@with_compat_node
@with_openstack_resource(OpenstackSecurityGroup)
def list_security_groups(openstack_resource, query=None):
    """
    List openstack security groups based on filters applied
    :param openstack_resource: Instance of current openstack security group
    :param kwargs query: Optional query parameters to be sent to limit
            the security groups being returned.
    """

    security_groups = openstack_resource.list(query)
    add_resource_list_to_runtime_properties(SECURITY_GROUP_OPENSTACK_TYPE,
                                            security_groups)


@with_compat_node
@with_openstack_resource(OpenstackSecurityGroup)
def creation_validation(openstack_resource):
    """
    This method is to check if we can create security group resource
    in openstack
    :param openstack_resource: Instance of current openstack security group
    """
    security_group_creation_validation(openstack_resource)
    ctx.logger.debug('OK: security group configuration is valid')
