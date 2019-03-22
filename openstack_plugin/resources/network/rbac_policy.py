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
from openstack_sdk.resources.networks import (OpenstackRBACPolicy,
                                              OpenstackNetwork,
                                              OpenstackSubnet,
                                              OpenstackPort)
from openstack_plugin.decorators import with_openstack_resource
from openstack_plugin.constants import (RESOURCE_ID,
                                        OPENSTACK_TYPE_PROPERTY,
                                        NETWORK_OPENSTACK_TYPE,
                                        RBAC_POLICY_OPENSTACK_TYPE,
                                        RBAC_POLICY_RELATIONSHIP_TYPE,
                                        QOS_POLICY_OPENSTACK_TYPE)

from openstack_plugin.utils import (reset_dict_empty_keys,
                                    merge_resource_config,
                                    validate_resource_quota,
                                    add_resource_list_to_runtime_properties,
                                    find_relationships_by_relationship_type)


def _get_rbac_policy_target_from_relationship():
    """
    Lookup target object that should apply rbac policy for and return it as
    the following format
    {
     'object_id': '9a332608-af04-4368-b696-3726a54f2a66'
     'object_type': 'network'
    }
    :return: Object info that contains details about object type & id
    """

    # Lookup the rbac policy relationship so that we can get the info that
    # we need to create rbac policy and apply it for target object
    rels = \
        find_relationships_by_relationship_type(
            ctx, RBAC_POLICY_RELATIONSHIP_TYPE
        )

    # It could be no relationship find for the current node context which
    # means that the node is not associated with any other node
    if len(rels) == 0:
        ctx.logger.info(
            'Resource for which RBAC policy may be applied '
            'not found using {0} relationship'
            .format(RBAC_POLICY_RELATIONSHIP_TYPE)
        )

        return {}

    # Since rbac policy allow only to be applied to one object at a time
    # then we cannot define link rbac policy node with multiple nodes via
    # "cloudify.relationships.openstack.rbac_policy_applied_to"
    elif len(rels) > 1:
        raise NonRecoverableError(
            'Multiple ({0}) resources for which RBAC policy may be applied '
            'found using relationship {1}'
            .format(
                len(rels),
                RBAC_POLICY_RELATIONSHIP_TYPE
            )
        )

    # Lookup the target instance in order to get the target object
    # runtime properties which represent "type" & "id"
    resource = rels[0].target.instance
    ctx.logger.info(
        '{0} resource for which RBAC policy may be applied '
        'found using {1} relationship)'
        .format(resource, RBAC_POLICY_RELATIONSHIP_TYPE)
    )

    # Get the instance runtime properties for both "id" & "type"
    resource_id = resource.runtime_properties.get(RESOURCE_ID)
    resource_type = resource.runtime_properties.get(OPENSTACK_TYPE_PROPERTY)

    # If we cannot find these attributes then we can skip that and depend on
    # the rbac policy to resolve "object_type" & "object_id"
    if not resource_id or not resource_type:
        ctx.logger.warn(
            'Found using relationship resource has not defined either '
            '"id" or "type" runtime_property. Skipping.'
        )

        return {}

    # Return the object info needed to be wrapped into API request when
    # create rbac request
    return {
        'object_type': resource_type,
        'object_id': resource_id
    }


def _validate_config_for_applied_rbac_resource(input_dict, target_object):
    """
    Validate that resource does not contain multiple definitions for rbac
    policy that allow user to specify them using properties, operation
    inputs and  relationship
    :param dict input_dict: Target object config provided via properties or
    operation inputs
    :param dict target_object: Target object config provided via relationship
    """
    if target_object:
        for key in target_object.keys():
            if input_dict and input_dict.get(key):
                raise NonRecoverableError(
                    'Multiple definitions of resource for which '
                    'RBAC policy should be applied. '
                    'You specified it both using properties / operation '
                    'inputs and relationship.'
                )


def _get_rbac_policy_target_object(openstack_resource, args):
    """
    Lookup the target object that need to apply rbac policy for
    :param openstack_resource: instance of openstack rbac policy resource
    :param dict args: RBAC policy configuration provided via task inputs
    :return dict: Object info that contains details about object type & id
      {
        'object_id': '9a332608-af04-4368-b696-3726a54f2a66'
        'object_type': 'network'

      }
    """
    # Try to lookup the object_type & object_id from relationships first
    object_info = _get_rbac_policy_target_from_relationship()

    # Validate the config rbac resources
    if object_info:
        for config in [openstack_resource.config, args]:
            _validate_config_for_applied_rbac_resource(config, object_info)

    return object_info


def _prepare_rbac_policy_object(openstack_resource, args):

    """
    Prepare and generate rbac policy which will be used to create RBAC policy
    This method mainly will do the following:

    1 - Try to lookup target object via realtionship in order to apply rbac
    policy
    2 - Merge provided config args with rbac policy node properties

    :param openstack_resource: instance of openstack rbac policy resource
    :param dict args: RBAC policy configuration provided via task inputs
    """

    # Try to lookup if there is any target object that should be apply rabc on
    target_object = _get_rbac_policy_target_object(openstack_resource, args)
    if target_object:
        openstack_resource.config['object_id'] = target_object['object_id']
        openstack_resource.config['object_type'] = target_object['object_type']

    # If there is no target object (No relationship exists) then we need to
    # check if the current node config contains all the info needed for
    # target object
    else:
        object_id = openstack_resource.cofig.get('object_id')
        object_type = openstack_resource.cofig.get('object_type')
        if not (object_id and object_type):
            raise NonRecoverableError(
                'Both object_id & object_type should be provided in order'
                ' to create rbac policy'
            )

    # Check to see if there are some configuration provided via operation
    # input so that we can merge them with volume config
    merge_resource_config(openstack_resource.config, args)


def _disable_dhcp_for_subnets(client_config, resource_id):
    """
    Disable dhcp for subnets associated with network so that rbac policy can
    be removed
    :param client_config: Openstack config required to make API calls
    :param resource_id:  resource_id: Resource id of the target object
    """

    network = OpenstackNetwork(client_config, logger=ctx.logger)
    network.resource_id = resource_id
    network_item = network.get()
    # Disable dhcp option for all attached subnets associated with
    # current network
    for subnet_id in network_item.subnet_ids:
        subnet = OpenstackSubnet(client_config, logger=ctx.logger)
        subnet.resource_id = subnet_id
        subnet_item = subnet.get()
        # Disable dhcp for subnets if its already enabled, since this
        # will prevent rbac policy from deletion
        if subnet_item.is_dhcp_enabled:
            subnet.update(new_config={'enable_dhcp': False})


def _clean_ports_from_network(client_config, resource_id):
    """
    Unset & clean ports associated with network
    :param client_config: Openstack config required to make API calls
    :param resource_id:  resource_id: Resource id of the target object
    """
    # The network could have another type of ports other than
    # "network:dhcp" that should be delete in order to be able to delete
    # rbac policy which can be controlled over "clean_ports" because
    # sometime ports are created using cloudify blueprints which can be
    # removed automatically whenever uninstall trigger. However, we may
    # need to remove ports ourselves if resource is not created using
    # cloudify
    port = OpenstackPort(client_config, logger=ctx.logger)
    for port_item in port.list(query={'network_id': resource_id}):
        port.resource_id = port_item.id
        port.update(new_config={'device_id': 'none'})
        port.delete()


def _clean_resources_from_target_object(client_config,
                                        resource_id,
                                        resource_type,
                                        disable_dhcp=False,
                                        clean_ports=False):
    """
    This merhod will help to clean ports and disable dhcp for subnets before
    delete rbac policy since cannot remove rbac policy before remove them
    :param dict client_config: Openstack config required to make API calls
    :param str resource_id: Resource id of the target object
    :param str resource_type: Resource type of the target object (network)
    :param bool disable_dhcp: Flag to allow disable dhcp for subnets
    :param bool clean_ports: Flag to allow unset & clear ports
    """

    # The type of the object that the RBAC policy affects. include qos-policy
    # or network.
    if resource_type == NETWORK_OPENSTACK_TYPE:
        if disable_dhcp:
            _disable_dhcp_for_subnets(client_config, resource_id)

        if clean_ports:
            _clean_ports_from_network(client_config, resource_id)

    elif resource_type == QOS_POLICY_OPENSTACK_TYPE:
        # TODO since qos-policy not support right now, this should be added
        #  later on
        pass


@with_openstack_resource(OpenstackRBACPolicy)
def create(openstack_resource, args):
    """
    Create openstack rbac policy instance
    :param openstack_resource: instance of openstack rbac policy resource
    """
    _prepare_rbac_policy_object(openstack_resource, args)
    created_resource = openstack_resource.create()
    ctx.instance.runtime_properties[RESOURCE_ID] = created_resource.id


@with_openstack_resource(OpenstackRBACPolicy)
def delete(openstack_resource):
    """
    Delete current openstack rbac policy instance
    :param openstack_resource: instance of openstack srbac policy resource
    """
    openstack_resource.delete()


@with_openstack_resource(OpenstackRBACPolicy)
def update(openstack_resource, args):
    """
    Update openstack rbac policy by passing args dict that contains the info
    that need to be updated
    :param openstack_resource: instance of openstack rbac policy resource
    :param args: dict of information need to be updated
    """
    args = reset_dict_empty_keys(args)
    openstack_resource.update(args)


@with_openstack_resource(OpenstackRBACPolicy)
def list_rbac_policies(openstack_resource, query=None):
    """
    List openstack rbac policies based on filters applied
    :param openstack_resource: Instance of current openstack rbac policy
    :param kwargs query: Optional query parameters to be sent to limit
            the rbac policies being returned.
    """

    rbac_policies = openstack_resource.list(query)
    add_resource_list_to_runtime_properties(RBAC_POLICY_OPENSTACK_TYPE,
                                            rbac_policies)


@with_openstack_resource(OpenstackRBACPolicy)
def find_and_delete(openstack_resource,
                    args,
                    disable_dhcp=False,
                    clean_ports=False):
    """
    This method will help to find rbac policy object and delete it.
    By Default "disable_dhcp" & "clean_ports" are set to False and they can
    be enabled in order to help clean ports and disable dhcp.

    :param openstack_resource: Instance of current openstack rbac policy
    :param dict args: RBAC policy object config
    :param bool disable_dhcp: Flag to allow disable dhcp for subnets
    :param bool clean_ports: Flag to allow unset & clear ports
    """

    _prepare_rbac_policy_object(openstack_resource, args)
    rbac_policy_config = openstack_resource.config

    # Since "id" will be set as part of the current node instance, we need
    # to remove it from the config since this operation main job is to find
    # rbac policy based on the configuration provided by operation task and
    # then remove it
    rbac_policy_config.pop('id', None)
    rbac_policies = openstack_resource.list()

    for rbac_policy in rbac_policies:
        # In order to find the rbac policy we need to filter the rbac policy
        # based on the following params
        # - object_type
        # - object_id
        # - action
        # - target_tenant

        # However, the response return from API server for listing rbac
        # policies return the following params
        # - id
        # - project_id
        # - action
        # - location
        # - object_id
        # - object_type
        # - name
        # - target_project_id

        # We care only about these config
        # - object_type
        # - object_id
        # - action
        # - target_project_id

        # We need to do a mapping between "target_project_id" and
        # "target_tenant" to do the comparison
        def _parse_item(item):
            return (item[0], item[1]) if item[0] != 'target_project_id'\
                else ('target_tenant', item[1])

        rbac_policy = dict(map(_parse_item, rbac_policy.iteritems()))
        if all(item in rbac_policy.items()
               for item in rbac_policy_config.items()):

            # Found the target object which should be deleted
            ctx.logger.info(
                'Found RBAC policy with ID: {0} - deleting ...'
                ''.format(rbac_policy['id'])
            )

            # Call clean method
            _clean_resources_from_target_object(
                openstack_resource.client_config,
                rbac_policy['object_id'],
                NETWORK_OPENSTACK_TYPE,
                disable_dhcp,
                clean_ports
            )
            # We need to delete the matched object
            openstack_resource.resource_id = rbac_policy['id']
            openstack_resource.delete()
            return

    ctx.logger.warn('No suitable RBAC policy found')


@with_openstack_resource(OpenstackRBACPolicy)
def creation_validation(openstack_resource):
    """
    This method is to check if we can create rbac policy resource in openstack
    :param openstack_resource: Instance of current openstack rbac policy
    """
    validate_resource_quota(openstack_resource, RBAC_POLICY_OPENSTACK_TYPE)
    ctx.logger.debug('OK: rbac policy configuration is valid')


@with_openstack_resource(OpenstackRBACPolicy)
def unlink_target_object(openstack_resource,
                         resource_id,
                         disable_dhcp=False,
                         clean_ports=False):
    """
    This task method is to clean resources associated with resource which
    are required to be removed before rbac policy get removed and this task
    would be useful on the following cases :

    1 - if resource type associated with rbac policy is network and has
      subnets with dhcp enabled, then in order to remove the rbac policy it
      is required to disable dhcb by passing "disable_dhcp" as "True"

    2 - If resource type associated with rbac policy is network and has
    ports that created outside cloudify, then we should unset these ports
    and delete them by passing "clean_ports" as "True"


   3 - If resource type associated with rbac policy is network and has both
     subnets with dhcp enabled & ports that created outside cloudify
     then we should disable dhcb and clean ports by passing
     "disable_dhcp" as "True" & "clean_ports" as "True"

   4 - If resource type associated with rbac policy is network and has
       ports that created inside cloudify, then we should not allow clean
       and unset ports since these are going to be deleted automatically as
       part of the install workflow, so based on that "clean_ports" should
       be passed as "False"

    :param openstack_resource: Instance of current openstack rbac policy
    :param str resource_id: Resource id of the target object (network)
    :param bool disable_dhcp: Flag to allow disable dhcp for subnets
    :param bool clean_ports: Flag to allow unset & clear ports
    """
    resource_type = \
        ctx.target.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY]

    _clean_resources_from_target_object(
        openstack_resource.client_config,
        resource_id,
        resource_type,
        disable_dhcp,
        clean_ports
    )
