
#########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
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
from cloudify.exceptions import NonRecoverableError
from openstack_plugin_common import (
    with_heat_client)


COMPLETE = 'CREATE_COMPLETE'
FAILED = 'CREATE_FAILED'
IN_PROGRESS = 'CREATE_IN_PROGRESS'

RETRY_AFTER = 10


def _check_status(heat_client, stack_id):
        reply = heat_client.stacks.get(stack_id)
        status = reply.stack_status
        if status == COMPLETE:
            return
        elif status == IN_PROGRESS:
            return ctx.operation.retry(
                message='Stack installation in progress',
                retry_after=RETRY_AFTER)
        elif status == FAILED:
            raise NonRecoverableError("Stack installation failed")
        else:
            raise NonRecoverableError("Unknown status: {}".format(status))


@operation
@with_heat_client
def create(heat_client, **kwargs):
    stack_id = ctx.instance.runtime_properties.get('stack_id')
    stack_name = ctx.node.id
    if stack_id:
        return _check_status(heat_client, stack_id)
    else:
        template = ctx.node.properties.get('template')
        template_url = ctx.node.properties.get('template_url')
        parameters = ctx.node.properties.get('parameters', {})
        if not template and not template_url:
            raise NonRecoverableError("Template and template_url not foud")
        downloaded_file_path = ctx.download_resource(template)
        template_content = open(downloaded_file_path).read()
        data = {"stack_name": stack_name,
                "parameters": parameters,
                "template": template_content,
                "template_url": template_url}
        result = heat_client.stacks.create(**data)
        ctx.instance.runtime_properties['stack_id'] = result['stack']['id']
        return _check_status(heat_client, result['stack']['id'])


@operation
@with_heat_client
def delete(heat_client, **kwargs):
    stack_id = ctx.instance.runtime_properties.get('stack_id')
    if not stack_id:
        raise NonRecoverableError("Stack_id not foud")
    heat_client.stacks.delete(stack_id)
