#########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
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

from openstack_plugin_common import (with_glance_client,
                                     get_resource_id,
                                     use_external_resource,
                                     delete_resource_and_runtime_properties,
                                     validate_resource,
                                     COMMON_RUNTIME_PROPERTIES_KEYS,
                                     OPENSTACK_ID_PROPERTY,
                                     OPENSTACK_TYPE_PROPERTY,
                                     OPENSTACK_NAME_PROPERTY)


IMAGE_OPENSTACK_TYPE = 'image'

RUNTIME_PROPERTIES_KEYS = COMMON_RUNTIME_PROPERTIES_KEYS


@operation
@with_glance_client
def create(glance_client, **kwargs):
    if use_external_resource(ctx, glance_client, IMAGE_OPENSTACK_TYPE):
        return

    image_dict = {
        'name': get_resource_id(ctx, IMAGE_OPENSTACK_TYPE)
    }
    img_properties = ctx.node.properties['image']
    image_dict.update({key: value for key, value in img_properties.iteritems()
                       if key != 'data'})
    _check_image()
    image = glance_client.images.create(**image_dict)

    try:
        img_path = img_properties.get('data', '')
        with open(img_path, 'rb') as image_file:
            glance_client.images.upload(image_id=image.id, image_data=image_file)
    except:
        _remove_protected(image.id)
        glance_client.images.delete(image_id=image.id)
        raise

    ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY] = image.id
    ctx.instance.runtime_properties[OPENSTACK_TYPE_PROPERTY] = \
        IMAGE_OPENSTACK_TYPE
    ctx.instance.runtime_properties[OPENSTACK_NAME_PROPERTY] = image.name


@operation
@with_glance_client
def delete(glance_client, **kwargs):
    _remove_protected(glance_client,
                      ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY])
    delete_resource_and_runtime_properties(ctx, glance_client,
                                           RUNTIME_PROPERTIES_KEYS)


@operation
@with_glance_client
def creation_validation(glance_client, **kwargs):
    validate_resource(ctx, glance_client, IMAGE_OPENSTACK_TYPE)
    _check_image()


def _check_image():
    img_path = ctx.node.properties['image'].get('data', '')
    try:
        with open(img_path, 'rb') as image_file:
            pass
    except IOError, e:
        raise NonRecoverableError(
            'Unable to open image file with path: "{}"'.format(img_path))


def _remove_protected(glance_client, img_id):
    if use_external_resource(ctx, glance_client, IMAGE_OPENSTACK_TYPE):
        return

    is_protected = ctx.node.properties['image'].get('protected', False)
    if is_protected:
        img_id = ctx.instance.runtime_properties[OPENSTACK_ID_PROPERTY]
        glance_client.images.update(img_id, protected=False)
