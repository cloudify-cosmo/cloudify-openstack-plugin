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

# Based on this documentation:
# https://docs.openstack.org/python-manilaclient/
# latest/user/api.html#module-manilaclient.

from manilaclient import client
from manilaclient.common.apiclient import exceptions

from ..common import OpenstackResource


class ManilaResource(OpenstackResource):

    def __init__(self, client_config, resource_config=None, logger=None):
        if 'client_version' not in client_config:
            client_config['client_version'] = '2'
        self.client_config = client_config
        self.configure_ssl()
        self.logger = logger
        self.connection = client.Client(**client_config)
        self.config = resource_config or {}
        self.name = self.config.get('name')
        self.resource_id =\
            None if 'id' not in self.config else self.config['id']
        self.validate_keystone_v3()

    def update_property(self, prop, value):
        setattr(self, prop, value)

    def update_id(self, value):
        self.update_property('id', value)

    @property
    def resource(self):
        return self.get()


class OpenstackShareNetwork(ManilaResource):

    service_type = 'manila'
    resource_type = 'network_share'

    def list(self):
        return self.connection.share_networks.list()

    def get(self):
        try:
            return self.find_network_share()
        except exceptions.NotFound:
            return

    def find_network_share(self, name_or_id=None):
        if not name_or_id:
            name_or_id = self.resource_id or self.name
        self.logger.debug(
            'Attempting to find this network share: {0}'.format(name_or_id))
        share = self.connection.share_networks.get(name_or_id)
        self.logger.debug(
            'Found network share with this result: {0}'.format(share))
        return share

    def create(self):
        self.logger.debug(
            'Attempting to create network share with these args: {0}'.format(
                self.config))
        share = self.connection.share_networks.create(**self.config)
        self.logger.debug(
            'Created network share with this result: {0}'.format(share))
        return share

    def delete(self):
        share = self.get()
        if not share:
            return
        self.logger.debug(
            'Attempting to delete this network share: {0}'.format(share))
        share.delete()
        self.logger.debug('Deleted network share .')


class OpenstackFileShare(ManilaResource):

    service_type = 'manila'
    resource_type = 'share'

    def list(self, query=None):
        query = query or {}
        return self.connection.shares.list(**query)

    def get(self):
        try:
            return self.find_share()
        except exceptions.NotFound:
            return

    def find_share(self, name_or_id=None):
        if not name_or_id:
            name_or_id = self.resource_id or self.name
        self.logger.debug(
            'Attempting to find this share: {0}'.format(name_or_id))
        share = self.connection.shares.get(name_or_id)
        self.logger.debug(
            'Found share with this result: {0}'.format(share))
        return share

    def create(self):
        self.logger.debug(
            'Attempting to create share with these args: {0}'.format(
                self.config))
        share = self.connection.shares.create(**self.config)
        self.logger.debug(
            'Created share with this result: {0}'.format(share))
        return share

    def update(self):
        share = self.get()
        if not share:
            return
        self.logger.debug(
            'Attempting to update share with these args: {0}'.format(
                self.config))
        result = share.update(**self.config)
        self.logger.debug(
            'Updated share with this result: {0}'.format(result))
        return result

    def delete(self):
        share = self.get()
        if not share:
            return
        self.logger.debug(
            'Attempting to delete this share: {0}'.format(share))
        response, body = share.delete()
        self.logger.debug(
            'Deleted share with this response: {0}, body {1}'.format(
                response, body))
        return response

    def allow(self, **params):
        self.logger.debug(
            'Attempting to allow share with these params: {0}'.format(
                params))
        share = self.get()
        if not share:
            return
        result = share.allow(**params)
        self.logger.debug(
            'Allowed share with this result: {0}'.format(result))
        return result

    def deny(self, var):
        self.logger.debug('Denying this share to {0}'.format(var))
        share = self.get()
        if not share:
            return
        result = share.deny(var)
        self.logger.debug(
            'Denied share with this result: {0}'.format(result))
        return result

    def get_locations(self):
        share = self.get()
        if not share:
            return
        return share.export_locations

    @property
    def ready(self):
        if self.resource:
            return self.resource.status == 'available'

    @property
    def error(self):
        if self.resource:
            return self.resource.status == 'error'

    @property
    def deleting(self):
        if self.resource:
            return self.resource.status == 'deleting'

    @property
    def delete_failed(self):
        if self.resource:
            return self.resource.status == 'error_deleting'
