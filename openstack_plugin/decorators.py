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

# Standard Imports
import sys

# Third party imports
from openstack import exceptions
from cloudify import ctx as CloudifyContext
from cloudify.exceptions import NonRecoverableError
from cloudify.utils import exception_to_error_cause

# Local imports
from openstack_plugin.compat import Compat
from openstack_plugin.utils \
    import (resolve_ctx,
            get_current_operation,
            prepare_resource_instance,
            use_external_resource,
            update_runtime_properties_for_operation_task,
            is_compat_node)

from openstack_plugin.constants import OPENSTACK_TYPE_PROPERTY


def with_openstack_resource(class_decl,
                            existing_resource_handler=None,
                            **existing_resource_kwargs):
    """
    :param class_decl: This is a class for the openstack resource need to be
    invoked
    :param existing_resource_handler: This is a method that handle any
    custom operation need to be done in case "use_external_resource" is set
    to true
    :param existing_resource_kwargs: This is an extra param that we may need
    to pass to the external resource  handler
    :return: a wrapper object encapsulating the invoked function
    """
    def wrapper_outer(func):
        def wrapper_inner(**kwargs):
            # Get the context for the current task operation
            ctx = kwargs.pop('ctx', CloudifyContext)

            # Resolve the actual context which need to run operation,
            # the context could be belongs to relationship context or actual
            # node context
            ctx_node = resolve_ctx(ctx)

            # Get the current operation name
            operation_name = get_current_operation()

            # Prepare the openstack resource that need to execute the
            # current task operation
            resource = \
                prepare_resource_instance(class_decl, ctx_node, kwargs)

            if use_external_resource(ctx_node, resource,
                                     existing_resource_handler,
                                     **existing_resource_kwargs):
                return
            try:
                kwargs['openstack_resource'] = resource
                func(**kwargs)
                update_runtime_properties_for_operation_task(operation_name,
                                                             ctx_node,
                                                             resource)
            except exceptions.SDKException as error:
                _, _, tb = sys.exc_info()
                raise NonRecoverableError(
                    'Failure while trying to request '
                    'Openstack API: {}'.format(error.message),
                    causes=[exception_to_error_cause(error, tb)])
        return wrapper_inner
    return wrapper_outer


def with_compat_node(func):
    """
    This decorator is used to transform nodes properties for openstack nodes
    with version 2.X to be compatible with new nodes support by version 3.x
    :param func: The decorated function
    :return: Wrapped function
    """
    def wrapper(**kwargs):
        ctx = kwargs.get('ctx', CloudifyContext)

        # Resolve the actual context which need to run operation,
        # the context could be belongs to relationship context or actual
        # node context
        ctx_node = resolve_ctx(ctx)
        # Check to see if we need to do properties transformation or not
        kwargs_config = {}
        if is_compat_node(ctx_node):
            compat = Compat(context=ctx_node, **kwargs)
            kwargs_config = compat.transform()

        if not kwargs_config:
            kwargs_config = kwargs
        func(**kwargs_config)
        # After this the resource should be created and we should have the
        # "id" runtime property set correctly
        # Get the "external_id" if it exists
        external_id = ctx_node.instance.runtime_properties.get('external_id')
        # This is the resource id for openstack 3.x nodes
        resource_id = ctx_node.instance.runtime_properties.get('id')
        if is_compat_node(ctx_node) and resource_id and not external_id:
            ctx_node.instance.runtime_properties['external_id']\
                = ctx_node.instance.runtime_properties['id']

        # Check if the 'routes' exists in 'kwargs_config' and override the
        # 'type' property to match 'routes'
        if 'routes' in kwargs_config:
            ctx_node.instance.runtime_properties[
                OPENSTACK_TYPE_PROPERTY] = 'routes'
    return wrapper


def with_multiple_data_sources(clean_duplicates_handler=None):
    def wrapper_outer(func):
        def wrapper_inner(config, **kwargs):
            # Check if the current node has "use_compact_node"
            if is_compat_node(CloudifyContext):
                kwargs['allow_multiple'] = True
            func(config, **kwargs)
            if kwargs.get('allow_multiple') and clean_duplicates_handler:
                clean_duplicates_handler(config)
        return wrapper_inner
    return wrapper_outer
