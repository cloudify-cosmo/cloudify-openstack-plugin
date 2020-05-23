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

# Standard imports
import sys
import copy
import logging
import base64
import inspect
import re


# Third part imports
import openstack.exceptions
from openstack._log import setup_logging
from IPy import IP
from cloudify import compute
from cloudify import ctx
from cloudify.exceptions import (NonRecoverableError, OperationRetry)
from cloudify.utils import exception_to_error_cause
from cloudify.constants import NODE_INSTANCE, RELATIONSHIP_INSTANCE

# Py2/3 compatibility
from openstack_sdk._compat import text_type


# Local imports
from openstack_plugin.constants import (
    PS_OPEN,
    PS_CLOSE,
    QUOTA_VALID_MSG,
    QUOTA_INVALID_MSG,
    INFINITE_RESOURCE_QUOTA,
    RESOURCE_ID,
    CONDITIONALLY_CREATED,
    USE_EXTERNAL_RESOURCE_PROPERTY,
    CREATE_IF_MISSING_PROPERTY,
    OPENSTACK_TYPE_PROPERTY,
    OPENSTACK_NAME_PROPERTY,
    OPENSTACK_EXTERNAL_RESOURCE,
    CLOUDIFY_NEW_NODE_OPERATIONS,
    CLOUDIFY_CREATE_OPERATION,
    CLOUDIFY_DELETE_OPERATION,
    USE_COMPACT_NODE,
    RBAC_POLICY_OPENSTACK_TYPE,
    NETWORK_OPENSTACK_TYPE,
    PORT_OPENSTACK_TYPE,
    KEY_USE_CFY_LOGGER,
    KEY_GROUPS,
    KEY_LOGGERS,
    DEFAULT_LOGGING_CONFIG,
    LOGGING_GROUPS
)


NODE_NAME_RE = re.compile('^(.*)_.*$')  # Anything before last underscore


class CloudifyLogHandler(logging.Handler):
    """
    A logging handler for Cloudify.
    A logger attached to this handler will result in logging being passed
    through to the Cloudify logger.
    """
    def __init__(self, cfy_logger):
        """
        Constructor.
        :param cfy_logger: current Cloudify logger
        """
        logging.Handler.__init__(self)
        self.cfy_logger = cfy_logger

    def emit(self, record):
        """
        Callback to emit a log record.
        :param record: log record to write
        :type record: logging.LogRecord
        """
        message = self.format(record)
        self.cfy_logger.log(record.levelno, message)


def find_relationships_by_node_type_hierarchy(ctx_node_instance, node_type):
    """
    Finds all specified relationships of the Cloudify
    instance where the related node type is of a specified type.
    :param ctx_node_instance: Cloudify node instance which is an instance of
     cloudify.context.NodeInstanceContext
    :param node_type: Cloudify node type to search node_ctx.relationships for
    :return: List of Cloudify relationships
    """
    return [target_rel for target_rel in ctx_node_instance.relationships
            if node_type in target_rel.target.node.type_hierarchy]


def find_relationships_by_openstack_type(_ctx, type_name):
    """
    This method will lookup relationships for cloudify node based on the
    type of the nodes which are connected to that node
    :param _ctx: Cloudify context instance cloudify.context.CloudifyContext
    :param str type_name: Node type which is connected to the current node
    :return: list of RelationshipSubjectContext
    """
    return [rel for rel in _ctx.instance.relationships
            if rel.target.instance.runtime_properties.get(
                OPENSTACK_TYPE_PROPERTY) == type_name]


def find_relationship_by_node_type(ctx_node_instance, node_type):
    """
    Finds a single relationship of the Cloudify
    instance where the related node type is of a specified type.
    :param ctx_node_instance: Cloudify node instance which is an instance of
     cloudify.context.NodeInstanceContext
    :param node_type: Cloudify node type to search node_ctx.relationships for
    :return: A Cloudify relationship or None
    """
    relationships = \
        find_relationships_by_node_type_hierarchy(ctx_node_instance, node_type)
    return relationships[0] if len(relationships) > 0 else None


def find_openstack_ids_of_connected_nodes_by_openstack_type(_ctx, type_name):
    """
    This method will return list of openstack ids for connected nodes
    associated with the current node instance
    :param _ctx: Cloudify context instance cloudify.context.CloudifyContext
    :param str type_name: Node type which is connected to the current node
    :return: List of openstack resource ids
    """
    return [rel.target.instance.runtime_properties[RESOURCE_ID]
            for rel in find_relationships_by_openstack_type(_ctx, type_name)]


def find_relationships_by_relationship_type(_ctx, type_name):
    """
    Find cloudify relationships by relationship type.
    Follows the inheritance tree.
    :param _ctx: Cloudify context instance cloudify.context.CloudifyContext
    :param type_name: desired relationship type derived
    from cloudify.relationships.depends_on.
    :return: list of RelationshipSubjectContext
    """

    return [rel for rel in _ctx.instance.relationships if
            type_name in rel.type_hierarchy]


def get_resource_id_from_runtime_properties(_ctx):
    """
    This method will lookup the resource id which is stored as part of
    runtime properties
    :param _ctx: Cloudify context instance cloudify.context.CloudifyContext
    :return: Resource id
    """
    return _ctx.instance.runtime_properties.get(RESOURCE_ID)


def resolve_node_ctx_from_relationship(_ctx):
    """
    This method is to decide where to get node from relationship context
    since this is not exposed correctly from cloudify
    :param _ctx: current cloudify context object
    :return: RelationshipSubjectContext instance
    """
    # Get the node_id for the current node in order to decide if that node
    # is source | target
    node_id = _ctx._context.get('node_id')

    source_node_id = _ctx.source._context.get('node_id')
    target_node_id = _ctx.target._context.get('node_id')

    if node_id == source_node_id:
        return _ctx.source
    elif node_id == target_node_id:
        return _ctx.target
    else:
        raise NonRecoverableError(
            'Unable to decide if current node is source or target')


def resolve_ctx(_ctx):
    """
    This method is to lookup right context instance which could be one of
    the following:
     1- Context for source relationship instance
     2- Context for target relationship instance
     3- Context for current node
    :param _ctx: current cloudify context object
    :return: This could be RelationshipSubjectContext or CloudifyContext
    instance
    """
    if _ctx.type == RELATIONSHIP_INSTANCE:
        return resolve_node_ctx_from_relationship(_ctx)
    if _ctx.type != NODE_INSTANCE:
        _ctx.logger.warn(
            'CloudifyContext is neither {0} nor {1} type. '
            'Falling back to {0}. This indicates a problem.'.format(
                NODE_INSTANCE, RELATIONSHIP_INSTANCE))
    return _ctx


def handle_userdata(existing_userdata):
    """
    This method will be responsible for handle user data provided by the
    user on the following cases:
    1. When user specify "user_data" to create server on openstack
    2. When "install_method" for agent is set to "Init-script" the plugin
     should be able to inject/update "user_data" for server
    :param existing_userdata:
    :return: final_userdata
    """
    # Check the agent init script so that it can be injected to the target
    # machine to install the agent daemon
    install_agent_userdata = ctx.agent.init_script()
    # Get the "os_family" type, by default all node instances extend
    # "cloudify.nodes.Compute" node will have "os_family" set to "Linux"
    # It can be override for Windows which is need to be handled differently
    os_family = ctx.node.properties['os_family']

    if not (existing_userdata or install_agent_userdata):
        return None

    if not existing_userdata:
        existing_userdata = ''
    elif not ctx.node.properties['encode_user_data']:
        return existing_userdata

    if install_agent_userdata and os_family == 'windows':

        # Get the powershell content from install_agent_userdata
        install_agent_userdata = \
            extract_powershell_content(install_agent_userdata)

        # Get the powershell content from existing_userdata
        # (If it exists.)
        existing_userdata_powershell = \
            extract_powershell_content(existing_userdata)

        # Combine the powershell content from two sources.
        install_agent_userdata = \
            '#ps1_sysnative\n{0}\n{1}\n{2}\n{3}\n'.format(
                PS_OPEN,
                existing_userdata_powershell,
                install_agent_userdata,
                PS_CLOSE)

        # Additional work on the existing_userdata.
        # Remove duplicate Powershell content.
        # Get rid of unnecessary newlines.
        existing_userdata = \
            existing_userdata.replace(
                existing_userdata_powershell,
                '').replace(
                    PS_OPEN,
                    '').replace(
                        PS_CLOSE,
                        '').strip()

    if not existing_userdata or existing_userdata.isspace():
        final_userdata = install_agent_userdata
    elif not install_agent_userdata:
        final_userdata =\
            compute.create_multi_mimetype_userdata([existing_userdata])
    else:
        final_userdata = compute.create_multi_mimetype_userdata(
            [existing_userdata, install_agent_userdata])

    final_userdata = base64.b64encode(final_userdata.encode('utf-8')).decode(
        'ascii')
    return final_userdata


def extract_powershell_content(string_with_powershell):
    """We want to filter user data for powershell scripts.
    However, Openstack allows only one segment that is Powershell.
    So we have to concat separate Powershell scripts into one.
    First we separate all Powershell scripts without their tags.
    Later we will add the tags back.
    """

    split_string = string_with_powershell.splitlines()

    if not split_string:
        return ''

    if split_string[0] == '#ps1_sysnative' or \
            split_string[0] == '#ps1_x86':
        split_string.pop(0)

    if PS_OPEN not in split_string:
        script_start = -1  # Because we join at +1.
    else:
        script_start = split_string.index(PS_OPEN)

    if PS_CLOSE not in split_string:
        script_end = len(split_string)
    else:
        script_end = split_string.index(PS_CLOSE)

    # Return everything between Powershell back as a string.
    return '\n'.join(split_string[script_start + 1:script_end])


def reset_dict_empty_keys(dict_object):
    """
    Reset empty values for object and convert it to None object so that we
    can us them when initiate API request
    :param dict_object: dict of properties need to be reset
    :return dict_object: Updated dict_object
    """
    for key, value in dict_object.items():
        # Value could be boolean type, we do not need to convert it and lose
        # the actual value
        if not (value or isinstance(value, bool)):
            dict_object[key] = None
    return dict_object


def update_runtime_properties(properties=None):
    """
    Update runtime properties for node instance
    :param properties: dict of properties need to be set for node instance
    """
    properties = properties or {}
    for key, value in properties.items():
        ctx.instance.runtime_properties[key] = value


def add_resource_list_to_runtime_properties(openstack_type_name, object_list):
    """
    Update runtime properties for node instance with list of available
    resources on openstack for certain openstack type
    :param openstack_type_name: openstack resource name type
    :param object_list: list of all available resources on openstack
    """
    objects = []
    for obj in object_list:
        if type(obj) not in [str, dict]:
            obj = obj.to_dict()
        objects.append(obj)

    key_list = '{0}_list'.format(openstack_type_name)

    # if the key already exists then we need to re-generate new data and
    # omits the old one if the list command multiple times
    if ctx.instance.runtime_properties.get(key_list):
        del ctx.instance.runtime_properties[key_list]

    ctx.instance.runtime_properties[key_list] = objects


def validate_resource_quota(resource, openstack_type):
    """
    Do a validation for openstack resource to make sure it is allowed to
    create resource based on available resources created and maximum quota
    :param resource: openstack resource instance
    :param openstack_type: openstack resource type
    """
    ctx.logger.info(
        'validating resource {0} (node {1})'
        ''.format(openstack_type, ctx.node.id)
    )
    if openstack_type != RBAC_POLICY_OPENSTACK_TYPE:
        openstack_type_plural = resource.resource_plural(openstack_type)
    else:
        openstack_type_plural = openstack_type

    resource_list = list(resource.list())

    # This is the available quota for provisioning the resource
    resource_amount = len(resource_list)

    # Log message to give an indication to the caller that there will be a
    # call trigger to fetch the quota for current resource
    ctx.logger.info(
        'Fetching quota for resource {0} (node {1})'
        ''.format(openstack_type, ctx.node.id)
    )

    # This represent the quota for the provided resource openstack type
    resource_quota = resource.get_quota_sets(openstack_type_plural)
    ctx.logger.debug(
        'Comparing resource_amount {0} to resource_quota {1}'.format(
            resource_amount, resource_quota))
    if resource_amount < resource_quota \
            or resource_quota == INFINITE_RESOURCE_QUOTA:
        ctx.logger.debug(
            QUOTA_VALID_MSG.format(
                openstack_type,
                ctx.node.id,
                openstack_type_plural,
                resource_amount,
                resource_quota)
        )
    else:
        err_message = \
            QUOTA_INVALID_MSG.format(
                openstack_type,
                ctx.node.id,
                openstack_type_plural,
                resource_amount,
                resource_quota
            )
        ctx.logger.error('VALIDATION ERROR: {0}'.format(err_message))
        raise NonRecoverableError(err_message)


def set_runtime_properties_from_resource(_ctx,
                                         openstack_resource):
    """
    Set openstack "type" & "name" as runtime properties for current cloudify
    node instance
    :param _ctx: Cloudify node instance which is could be an instance of
    RelationshipSubjectContext or CloudifyContext
    :param openstack_resource: Openstack resource instance
    """
    if _ctx and openstack_resource:
        _ctx.instance.runtime_properties[
            OPENSTACK_TYPE_PROPERTY] = openstack_resource.resource_type

        _ctx.instance.runtime_properties[
            OPENSTACK_NAME_PROPERTY] = openstack_resource.name


def unset_runtime_properties_from_instance(_ctx):
    """
    Unset all runtime properties from node instance when delete operation
    task if finished
    :param _ctx: Cloudify node instance which is could be an instance of
    RelationshipSubjectContext or CloudifyContext
    """
    for key in list(_ctx.instance.runtime_properties.keys()):
        del _ctx.instance.runtime_properties[key]


def prepare_resource_instance(class_decl, _ctx, kwargs):
    """
    This method used to prepare and instantiate instance of openstack resource
    So that it can be used to make API request to execute required operations
    :param class_decl: Class name of the resource instance we need to create
    :param _ctx: Cloudify node instance which is could be an instance of
    RelationshipSubjectContext or CloudifyContext
    :param kwargs: Some config contains data for openstack resource that
    could be provided via input task operation
    :return: Instance of openstack resource
    """
    def get_property_by_name(property_name):
        property_value = None
        if _ctx.node.properties.get(property_name):
            property_value = \
                _ctx.node.properties.get(property_name)

        if _ctx.instance.runtime_properties.get(property_name):
            if isinstance(property_value, dict):
                property_value.update(
                    _ctx.instance.runtime_properties.get(
                        property_name))
            else:
                property_value = \
                    _ctx.instance.runtime_properties.get(
                        property_name)

        if kwargs.get(property_name):
            kwargs_value = kwargs.pop(property_name)
            if isinstance(property_value, dict):
                property_value.update(kwargs_value)
            else:
                return kwargs_value
        return property_value

    client_config = get_property_by_name('client_config')
    resource_config = get_property_by_name('resource_config')

    # If this arg is exist, that means user
    # provide extra/optional configuration for the defined node
    extra_resource_config = resource_config.pop('kwargs', None)
    if extra_resource_config:
        resource_config.update(extra_resource_config)

    # If name property is provided for the resource but it does not contain
    # any value, then we should generate a name based on the type of the
    # resource
    name = get_resource_name(_ctx, class_decl.resource_type)
    if name:
        resource_config['name'] = name

    # If this arg is exist, that means user
    # provide extra/optional client configuration for the defined node
    extra_client_config = client_config.pop('kwargs', None)
    if extra_client_config:
        client_config.update(extra_client_config)

    # Check if resource_id is part of runtime properties so that we
    # can add it to the resource_config
    if RESOURCE_ID in _ctx.instance.runtime_properties:
        resource_config['id'] = \
            _ctx.instance.runtime_properties[RESOURCE_ID]

    # Setup logging before init the Cloud resource
    setup_openstack_logging(client_config, ctx.logger)
    resource = class_decl(client_config=client_config,
                          resource_config=resource_config,
                          logger=ctx.logger)

    return resource


def update_runtime_properties_for_operation_task(operation_name,
                                                 _ctx,
                                                 openstack_resource=None):
    """
    This method will update runtime properties for node instance based on
    the operation task being running
    :param str operation_name:
    :param _ctx: Cloudify node instance which is could be an instance of
    RelationshipSubjectContext or CloudifyContext
    :param openstack_resource: Openstack resource instance
    """

    # Set runtime properties for "name" & "type" when current
    # operation is "create", so that they can be used later on
    if operation_name == CLOUDIFY_CREATE_OPERATION:
        set_runtime_properties_from_resource(_ctx,
                                             openstack_resource)
    # Clean all runtime properties for node instance when current operation
    # is delete
    elif operation_name == CLOUDIFY_DELETE_OPERATION:
        unset_runtime_properties_from_instance(_ctx)


def lookup_remote_resource(_ctx, openstack_resource):
    """
    This method will try to lookup openstack remote resource based on the
    instance type
    :param _ctx Cloudify node instance which is could be an instance of
    RelationshipSubjectContext or CloudifyContext
    :param openstack_resource: Instance derived from "OpenstackResource",
    it could be "OpenstackNetwork" or "OpenstackRouter" ..etc
    :return: Remote resource instance derived from openstack.resource.Resource
    """

    try:
        # Get the remote resource
        remote_resource = openstack_resource.get()
    except openstack.exceptions.SDKException as error:
        _, _, tb = sys.exc_info()
        # If external resource does not exist then try to create it instead
        # of failed, when "create_if_missing" is set to "True"
        if is_create_if_missing(_ctx):
            _ctx.instance.runtime_properties[CONDITIONALLY_CREATED] = True
            # Since openstack SDK does not allow to have "id" on the payload
            # request, "id" must be pop from openstack resource config so
            # that it cannot be sent when trying to create API
            openstack_resource.config.pop('id', None)
            openstack_resource.resource_id = None
            return None
        raise NonRecoverableError(
            'Failure while trying to request '
            'Openstack API: {}'.format(error.message),
            causes=[exception_to_error_cause(error, tb)])
    return remote_resource


def is_external_resource(_ctx):
    """
    This method is to check if the current node is an external openstack
    resource or not
    :param _ctx Cloudify node instance which is could be an instance of
    RelationshipSubjectContext or CloudifyContext
    :return bool: Return boolean flag to indicate if it is external or not
    """
    return True if \
        _ctx.node.properties.get(USE_EXTERNAL_RESOURCE_PROPERTY) else False


def is_compat_node(_ctx):
    """
    This method is to check if the current node need to be converted to
    openstack version 3.0.0 node
    :param _ctx: Cloudify context cloudify.context.CloudifyContext
    :return bool:  Return boolean flag to indicate if it has
    "use_compact_node" property or not
    """
    return True if _ctx.node.properties.get(USE_COMPACT_NODE) else False


def is_create_if_missing(_ctx):
    """
    This method is to check if the current node has a "create_if_missing"
    property in order to create resource even when "use_external_resource"
    is set to "True"
    resource or not
    :param _ctx Cloudify node instance which is could be an instance of
    RelationshipSubjectContext or CloudifyContext
    :return bool: Return boolean flag in order to decided if we should
    create external resource or not
    """
    return True if \
        _ctx.node.properties.get(CREATE_IF_MISSING_PROPERTY) else False


def is_external_relationship(_ctx):
    """
    This method is to check if both target & source nodes are external
    resources with "use_external_resource"
    :param _ctx: Cloudify context cloudify.context.CloudifyContext
    :return bool: Return boolean flag in order to decide if both resources
    are external
    """
    if is_external_resource(_ctx.source) and is_external_resource(_ctx.target):
        return True
    return False


def is_external_relationship_not_conditionally_created(_ctx):
    """
    This method is to check if the relationship between two nodes are
    external and not conditional created "create_if_missing" is set to
    "False" to the node which in turn does not have "conditionally_created"
    runtime property for the node instance
    :param _ctx: Cloudify context cloudify.context.CloudifyContext
    :return bool: Return boolean to indicate if both source/target are
    external resources and do not have "conditionally_created" runtime property
    """
    source_conditional_created = \
        _ctx.source.instance.runtime_properties.get(CONDITIONALLY_CREATED)

    target_conditional_created = \
        _ctx.target.instance.runtime_properties.get(CONDITIONALLY_CREATED)

    return \
        is_external_resource(ctx.source) and is_external_resource(ctx.target)\
        and not (source_conditional_created or target_conditional_created)


def use_external_resource(_ctx,
                          openstack_resource,
                          existing_resource_handler=None,
                          **kwargs):
    """
    :param _ctx Cloudify node instance which is could be an instance of
    RelationshipSubjectContext or CloudifyContext
    :param openstack_resource: Openstack resource instance
    :param existing_resource_handler: Callback handler that used to be
    called in order to execute custom operation when "use_external_resource" is
    enabled
    :param kwargs: Any extra param passed to the existing_resource_handler
    """
    # The cases when it is allowed to run operation tasks for resources
    # 1- When "use_external_resource=False"
    # 2- When "create_if_missing=True" and "use_external_resource=True"
    # 3- When "use_external_resource=True" and the current operations
    # are not included in the following operation list
    #   - "cloudify.interfaces.lifecycle.create"
    #   - "cloudify.interfaces.lifecycle.configure"
    #   - "cloudify.interfaces.lifecycle.start"
    #   - "cloudify.interfaces.lifecycle.stop"
    #   - "cloudify.interfaces.lifecycle.delete"
    #   - "cloudify.interfaces.validation.creation"

    # 4- When "use_external_resource=True" for (source|target) node node but
    # "use_external_resource=False" for (target|source) node for the
    # following relationship operations:
    #   - "cloudify.interfaces.relationship_lifecycle.preconfigure"
    #   - "cloudify.interfaces.relationship_lifecycle.postconfigure"
    #   - "cloudify.interfaces.relationship_lifecycle.establish"
    #   - "cloudify.interfaces.relationship_lifecycle.unlink"

    # Run custom operation When "existing_resource_handler" is not None,
    # so that it helps to validate or run that operation for external
    # existing resource in the following cases only:

    # 1- When "use_external_resource=True" for the following tasks:
    #   - "cloudify.interfaces.lifecycle.create"
    #   - "cloudify.interfaces.lifecycle.configure"
    #   - "cloudify.interfaces.lifecycle.start"
    #   - "cloudify.interfaces.lifecycle.stop"
    #   - "cloudify.interfaces.lifecycle.delete"
    #   - "cloudify.interfaces.validation.creation"

    # 2- When "use_external_resource=True" for both source & target node on
    # the for the following operations:
    #   - "cloudify.interfaces.relationship_lifecycle.preconfigure"
    #   - "cloudify.interfaces.relationship_lifecycle.postconfigure"
    #   - "cloudify.interfaces.relationship_lifecycle.establish"
    #   - "cloudify.interfaces.relationship_lifecycle.unlink"

    # Return None to indicate that this is the resource is not created and
    # we should continue and run operation node tasks
    if not is_external_resource(_ctx):
        return None

    ctx.logger.info('Using external resource {0}'.format(RESOURCE_ID))
    # Get the current operation name
    operation_name = get_current_operation()

    # Try to lookup remote resource
    remote_resource = lookup_remote_resource(_ctx, openstack_resource)
    if remote_resource:
        # Set external resource as runtime property for create operation
        set_external_resource(
            _ctx, openstack_resource, [CLOUDIFY_CREATE_OPERATION]
        )

    # Check if the current node instance is conditional created or not
    is_create = _ctx.instance.runtime_properties.get(CONDITIONALLY_CREATED)
    # Check if context type is "relationship-instance" and to check if both
    # target and source are not external
    is_not_external_rel = \
        ctx.type == RELATIONSHIP_INSTANCE and not is_external_relationship(ctx)

    if is_create or is_not_external_rel:
        return None

    if remote_resource:
        openstack_resource.resource_id = remote_resource.id
    # Just log message that we cannot delete resource since it is an
    # external resource
    if operation_name == CLOUDIFY_CREATE_OPERATION:
        _ctx.logger.info(
            'not creating resource {0}'
            ' since an external resource is being used'
            ''.format(remote_resource.name))
        _ctx.instance.runtime_properties[RESOURCE_ID] = remote_resource.id
        if hasattr(remote_resource, 'name') and remote_resource.name:
            openstack_resource.name = remote_resource.name
    # Just log message that we cannot delete resource since it is an
    # external resource
    elif operation_name == CLOUDIFY_DELETE_OPERATION:
        _ctx.logger.info(
            'not deleting resource {0}'
            ' since an external resource is being used'
            ''.format(remote_resource.name))

    # Check if we need to run custom operation for already existed
    # resource for operation task
    if existing_resource_handler:
        # We may need to send the "openstack_resource" to the
        # existing resource handler and in order to do that we may
        # need to check if the resource is already there or not
        func_args = inspect.getargspec(existing_resource_handler).args
        if 'openstack_resource' in func_args:
            kwargs['openstack_resource'] = openstack_resource

        existing_resource_handler(**kwargs)

    # Check which operations are allowed to execute when
    # "use_external_resource" is set to "True" and "node_type" is instance
    if ctx.type == NODE_INSTANCE\
            and allow_to_run_operation_for_external_node(operation_name):
        return None
    else:
        # Update runtime properties for operation create | delete operations
        update_runtime_properties_for_operation_task(operation_name,
                                                     _ctx,
                                                     openstack_resource)
        # Return instance of the external node
        return openstack_resource


def get_snapshot_name(object_type, snapshot_name, snapshot_incremental):
    """
    Generate snapshot name
    :param str object_type: Object type that snapshot is generated for (vm,
    disk, ..etc)
    :param str snapshot_name: Snapshot name
    :param bool snapshot_incremental: Flag to create an incremental snapshots
     or full backup
    :return: Snapshot name
    """
    return "{0}-{1}-{2}-{3}".format(
        object_type, get_resource_id_from_runtime_properties(ctx),
        snapshot_name, "increment" if snapshot_incremental else "backup")


def get_resource_name(_ctx, type_name):
    """
    This will return resource name and will generate a name based on
    resource type if resource name is missing
    :param _ctx: Cloudify node instance which is could be an instance of
    RelationshipSubjectContext or CloudifyContext
    :param str type_name: Resource type (server | server_group ...etc)
    :return str: resource name

    **Note**: Not all openstack resources accept "name" property, so this
    method will return None, if "resource_config" does not contain "name"
    """
    resource_config = _ctx.node.properties.get('resource_config')
    # This check means that resource_config is None or resource config does
    # not have 'name' at all, in case it contains the "name" but the default
    # is empty, then we need to generate a new name for that resource since
    # it support name
    if not resource_config or 'name' not in resource_config:
        return None

    elif resource_config.get('name'):
        return resource_config['name']

    dep_id = _ctx.deployment.id\
        if hasattr(_ctx, 'deployment') else ctx.deployment.id
    node_instance_id = _ctx.instance.id.replace('_', '-')
    name = '{0}-{1}-{2}'.format(type_name,
                                dep_id,
                                node_instance_id)
    return name


def get_current_operation():
    """ Get the current task operation from current cloudify context
    :return str: Operation name
    """
    return ctx.operation.name


def get_ready_resource_status(resource,
                              resource_type,
                              status,
                              error_statuses):
    """
    This method is to check what is the current status of openstack resource
    when running certain operation on it and need to make sure that the
    resource's operation is done
    :param resource: Current instance of openstack resource
    :param str resource_type: Resource type need to check status for
    :param str status: desired status need to check the resource on
    :param list error_statuses: List of error statuses that we should raise
     error about if the remote openstack resource matches them
    :return: Instance of the current openstack object contains the updated
    status and boolean flag to mark it as updated or not
    """
    # Get the last updated instance in order to start comparison based
    # on the remote status with the desired one that resource should be in
    openstack_resource = resource.get()

    # If the remote status of the current object matches one of error
    # statuses defined to this method, then a NonRecoverableError must
    # be raised
    if openstack_resource.status in error_statuses:
        raise NonRecoverableError('{0} {1} is in error state'
                                  ''.format(resource_type,
                                            openstack_resource.id))

    # Check if the openstack resource match the desired status
    if openstack_resource.status == status:
        return openstack_resource, True

    # The object is not ready yet
    return openstack_resource, False


def wait_until_status(resource,
                      resource_type,
                      status,
                      error_statuses):
    """
    This method is build in order to check the status of the openstack
    resource and whether is is ready to be used or not
    :param resource: Current instance of openstack resource
    :param str resource_type: Resource type need to check status for
    :param str status: desired status need to check the resource on
    :param list error_statuses: List of error statuses that we should raise
     error about if the remote openstack resource matches them
    :return: Instance of the current openstack object contains the updated
    status
    """
    # Check the openstack resource status
    openstack_resource, ready = get_ready_resource_status(resource,
                                                          resource_type,
                                                          status,
                                                          error_statuses)
    if ready and openstack_resource:
        return openstack_resource
    else:
        message = '{0} {1} current state not ready: {2}'\
                .format(resource_type,
                        openstack_resource.id,
                        openstack_resource.status)

        raise OperationRetry(message)


def merge_resource_config(resource_config, config):
    """
    This method will merge configuration between resource configuration and
    any user input configuration
    :param dict resource_config: Resource configuration required to create
    resource in openstack
    :param dict config: User configuration that could merge/override with
    resource configuration
    """
    if all(item and isinstance(item, dict)
           for item in [resource_config, config]):
        resource_config.update(**config)


def generate_attachment_volume_key(prefix, volume_id, server_id):
    """
    This method helps to generate attachment volume key which can be used as
    runtime property when running attaching/detaching volume from/to server
    :param str prefix: Any prefix that could be added to the the key
    :param str volume_id: Unique volume id
    :param str server_id: Unique server id
    :return str: attachment volume key
    """
    if all([prefix, volume_id, server_id]):
        return '{0}-{1}-{2}'.format(prefix, volume_id, server_id)

    _ctx = resolve_ctx(ctx)
    return '{0}-attachment-volume'.format(_ctx.instance.id)


def assign_resource_payload_as_runtime_properties(_ctx,
                                                  payload,
                                                  resource_type):
    """
    Store resource configuration in the runtime
    properties and cleans any potentially sensitive data.
    :param _ctx: Cloudify context cloudify.context.CloudifyContext
    :param dict payload: The payload object for resource
    :param str resource_type: Resource openstack type
    """
    if all([getattr(ctx, 'instance'), payload, resource_type]):
        if resource_type not in ctx.instance.runtime_properties:
            ctx.instance.runtime_properties[resource_type] = {}
        for key, value in payload.items():
            if key not in ['user_data', 'adminPass']:
                ctx.instance.runtime_properties[resource_type][key] = value


def allow_to_run_operation_for_external_node(operation_name):
    """
    This method to check if an a current operation is allowed for external
    node that has flag "use_external_resource" set "True"
    :param (str) operation_name: The cloudify operation name for node
    :return bool: Flag to indicate whether or not it is allowed to run
    operation for the external node
    """
    if operation_name not in CLOUDIFY_NEW_NODE_OPERATIONS:
        return True
    return False


def remove_duplicates_items(items):
    """
    This method will clean duplicates items (dict) from list
    :param items: List of dicts
    :return: Updated list that without duplicate items
    """
    return [dict(t) for t in {tuple(d.items()) for d in items}]


def validate_ip_or_range_syntax(_ctx, address):
    """
    This method will check if provided address is valid or not
    :param _ctx: Cloudify context cloudify.context.CloudifyContext
    :param str address: Provided address
    """
    _ctx.logger.debug('Checking if {0} is a valid address'.format(address))
    try:
        IP(address)
        _ctx.logger.debug('OK:{0} is a valid address.'.format(address))
    except ValueError as e:
        err = ('{0} is not a valid address;{1}'.format(address, e))
        _ctx.logger.error('VALIDATION ERROR:{0}'.format(err))
        raise NonRecoverableError(err)


def get_target_node_from_capabilities(node_name):
    """
    This method will use cloudify context capabilities in order to find
    target node
    :param str node_name: Node name
    :return tuple: Return tuple that contains node_id with node instance
    runtime properties for target node if it exists
    """
    result = None
    caps = ctx.capabilities.get_all()
    for node_id in caps:
        match = NODE_NAME_RE.match(node_id)
        if match:
            candidate_node_name = match.group(1)
            if candidate_node_name == node_name:
                if result:
                    raise NonRecoverableError(
                        "More than one node named '{0}' "
                        "in capabilities".format(node_name))
                result = (node_id, caps[node_id])
    if not result:
        raise NonRecoverableError(
            "Could not find node named '{0}' "
            "in capabilities".format(node_name))
    return result


def update_runtime_properties_for_node_v2(ctx_node, kwargs):
    """
    This method will set basic runtime properties for node instance which
    are external_id, external_name for the node instance
    :param ctx_node: This could be RelationshipSubjectContext
     or CloudifyContext instance depend if it is a normal relationship
     operation or node operation
    :param dict kwargs: kwargs config for openstack v2
    """

    # At this point, the resource should be created and we should have the
    # "id" runtime property set correctly
    # Get the "external_id" if it exists
    external_id = ctx_node.instance.runtime_properties.get('external_id')
    # Get the "external_name" if it exists
    external_name = ctx_node.instance.runtime_properties.get('external_name')
    # Get the "external_type" if it exists
    external_type = ctx_node.instance.runtime_properties.get('external_type')
    # This is the resource id for openstack 3.x nodes
    resource_id = ctx_node.instance.runtime_properties.get('id')
    # This is the resource name for openstack 3.x nodes
    resource_name = ctx_node.instance.runtime_properties.get('name')
    # This is the resource type for openstack 3.x nodes
    resource_type = ctx_node.instance.runtime_properties.get('type')
    # Only apply this of the current node is compat node and it is marked as
    # external resource and it is not conditionally created
    is_created = \
        ctx_node.instance.runtime_properties.get(CONDITIONALLY_CREATED)

    if is_compat_node(ctx_node) and\
            is_external_resource(ctx_node) and not is_created:

        if resource_id and not external_id:
            ctx_node.instance.runtime_properties['external_id'] = resource_id

        if resource_name and not external_name:
            ctx_node.instance.runtime_properties['external_name'] = \
                resource_name

        if resource_type and not external_type:
            ctx_node.instance.runtime_properties['external_type'] = \
                resource_type

    # Check if the 'routes' exists in 'kwargs_config' and override the
    # 'type' property to match 'routes'
    if 'routes' in kwargs:
        ctx_node.instance.runtime_properties[
            OPENSTACK_TYPE_PROPERTY] = 'routes'


def set_external_resource(ctx_node, resource, target_operations):
    """
    This method will set external resource as runtime property for node
    instance
    :param ctx_node: This could be RelationshipSubjectContext
     or CloudifyContext instance depend if it is a normal relationship
     operation or node operation
    :param resource:  Instance of openstack resource
    :param target_operations: Operations allowed to set "external_resource"
    runtime property
    """
    # Save the external resource as runtime property in the following
    # operations:
    # 1. cloudify.interfaces.lifecycle.create
    # 2. cloudify.interfaces.operations.update
    # 3. cloudify.interfaces.operations.update_project
    if is_external_resource(ctx_node):
        operation_name = get_current_operation()
        remote_resource = resource.get()
        if operation_name in target_operations:
            ctx_node.instance.runtime_properties[OPENSTACK_EXTERNAL_RESOURCE]\
                = remote_resource


def get_networks_from_relationships(_ctx):
    """
    This method will return list of openstack ids for connected nodes
    associated with the current node instance
    :param _ctx: Cloudify context instance cloudify.context.CloudifyContext
    :return: List of networks objects
    """
    networks = []
    for rel in _ctx.instance.relationships:
        network = {}
        type_name = rel.target.instance.runtime_properties.get(
                OPENSTACK_TYPE_PROPERTY)
        resource_id = rel.target.instance.runtime_properties.get(RESOURCE_ID)
        if type_name == NETWORK_OPENSTACK_TYPE:
            network['uuid'] = resource_id
            networks.append(network)
        elif type_name == PORT_OPENSTACK_TYPE:
            network[PORT_OPENSTACK_TYPE] = resource_id
            networks.append(network)
    return networks


def get_security_groups_from_relationships(_ctx):
    """
    This method will return list of openstack security groups for connected
    nodes associated with the current node instance
    :param _ctx: Cloudify context instance cloudify.context.CloudifyContext
    :return: List of security groups objects
    """
    security_groups = []
    for rel in find_relationships_by_openstack_type(_ctx, 'security_group'):
        resource_id = rel.target.instance.runtime_properties.get(RESOURCE_ID)
        security_groups.append({
            'id': resource_id
        })
    return security_groups


def setup_openstack_logging(client_config, logger):
    # Get the logging object
    logging_config = client_config.pop('logging', dict())
    # Get a flag in order to check if we should redirect all the logs to
    # the cloudify logs
    if KEY_USE_CFY_LOGGER not in logging_config:
        use_cfy_logger = True
    else:
        use_cfy_logger = logging_config.get(KEY_USE_CFY_LOGGER)
    # Get group of logging we want to configure them and update their
    # handler as cloudify handler
    groups_config = logging_config.get(KEY_GROUPS, {})
    # Get any custom logger that want also to configure them
    loggers_config = logging_config.get(KEY_LOGGERS, {})

    # Get a copy of the default configuration for the logging of openstack
    final_logging_cfg = copy.deepcopy(DEFAULT_LOGGING_CONFIG)

    if use_cfy_logger:
        final_logging_cfg[KEY_USE_CFY_LOGGER] = use_cfy_logger
    else:
        use_cfy_logger = final_logging_cfg[KEY_USE_CFY_LOGGER]
    final_logging_cfg[KEY_GROUPS].update(groups_config)
    final_logging_cfg[KEY_LOGGERS].update(loggers_config)
    # Prepare mapping between logger names and logging levels.
    configured_loggers = {
        v: final_logging_cfg[KEY_GROUPS][k] for
        k, values in LOGGING_GROUPS.items() for v in values
    }
    # Update the final configuration logging for openstack
    configured_loggers.update(final_logging_cfg[KEY_LOGGERS])

    # After checking how openstack sdk handle logging it seems that
    # openstack & keystoneauth have the same level passed when setup the
    # logging, more info can be checked
    # 1. https://github.com/openstack/openstacksdk/blob/master/openstack/_log.py#L106 # NOQA
    # 2. https://github.com/openstack/openstacksdk/blob/master/openstack/_log.py#L107 # NOQA
    # 3. https://docs.openstack.org/openstacksdk/latest/user/guides/logging.html#python-logging # NOQA
    os_level = final_logging_cfg[KEY_GROUPS]['openstack']
    configured_loggers.update({
        'keystoneauth': os_level,
        'keystoneauth.discovery': logging.WARNING,
        'keystoneauth.identity.base': logging.WARNING,
        'keystoneauth.identity.generic.base': logging.WARNING,
    })
    # Check if it is allowed to redirect openstack logs to cloudify
    ctx_log_handler = CloudifyLogHandler(logger) if use_cfy_logger else None

    # Check each logger with is logging level so that we can add for
    # each logger the cloudify handler to log all events there
    for logger_name, logger_level in configured_loggers.items():
        # Before set the log make sure to convert it to upper case
        is_str = isinstance(logger_level, str)\
                 or isinstance(logger_level, text_type)
        if is_str:
            logger_level = logger_level.upper()
        setup_logging(logger_name, [ctx_log_handler], logger_level)
