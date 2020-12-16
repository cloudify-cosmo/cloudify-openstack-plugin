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

from ..common import OpenstackResource


class OpenstackSharedFileSystem(OpenstackResource):

    service_type = 'shared_file_system'
    resource_type = 'share'

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

    def list(self, query=None):
        query = query or {}
        return self.connection.shares.list(**query)

    def get(self):
        return self.find_share()

    def find_share(self, name_or_id=None):
        if not name_or_id:
            name_or_id = self.name if not \
                self.resource_id else self.resource_id
        self.logger.debug(
            'Attempting to find this share: {0}'.format(name_or_id))
        share = self.connection.shares.get(name_or_id)
        self.logger.debug(
            'Found volume with this result: {0}'.format(share))
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
        self.logger.debug(
            'Attempting to update share with these args: {0}'.format(
                self.config))
        result = share.update(**self.config)
        self.logger.debug(
            'Updated share with this result: {0}'.format(result))
        return result

    def delete(self):
        share = self.get()
        self.logger.debug(
            'Attempting to delete this volume: {0}'.format(share))
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
        result = share.allow(**params)
        self.logger.debug(
            'Allowed share with this result: {0}'.format(result))
        return result

    def deny(self, var):
        self.logger.debug('Denying this share to {0}'.format(var))
        share = self.get()
        result = share.deny(var)
        self.logger.debug(
            'Denied share with this result: {0}'.format(result))
        return result

    def get_locations(self):
        share = self.get()
        return share.export_locations
