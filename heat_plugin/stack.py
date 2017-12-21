
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


@operation
@with_heat_client
def create(heat_client, **kwargs):
    template = ctx.node.properties.get('template')
    # tenant_id = heat_client.service_catalog.get_tenant_id()
    if not template:
        raise NonRecoverableError("Template not foud")
    data = {}
    downloaded_file_path = \
                    ctx.download_resource('template')
    result = heat_client.stacks.create(data)


@operation
@with_heat_client
def delete(heat_client, **kwargs):
    pass
