# #######
# Copyright (c) 2020 Cloudify Platform Ltd. All rights reserved
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
# https://docs.openstack.org/openstacksdk/latest/user/proxies/compute.html.

# Local imports
from openstack_sdk.common import OpenstackResource


class OpenstackZone(OpenstackResource):
    service_type = 'dns'
    resource_type = 'zone'

    def get(self):
        zone = self.find_zone()
        return zone

    def find_zone(self, name_or_id=None):
        if not name_or_id:
            name_or_id = self.name if not\
                self.resource_id else self.resource_id
        self.logger.debug(
            'Attempting to find this zone: {0}'.format(name_or_id))
        zone = self.connection.dns.find_zone(
            name_or_id, ignore_missing=False
        )
        self.logger.debug(
            'Found zone with this result: {0}'.format(zone))
        return zone

    def create(self):
        self.logger.debug(
            'Attempting to create zone with these args: {0}'.format(
                self.config))
        zone = self.connection.dns.create_zone(**self.config)
        self.logger.info(
            'Created zone with this result: {0}'.format(zone))
        return zone

    def delete(self):
        zone = self.get()
        self.logger.debug(
            'Attempting to delete this zone: {0}'.format(zone))
        result = self.connection.dns.delete_zone(zone)
        self.logger.debug(
            'Deleted zone with this result: {0}'.format(result))
        return result


class OpenstackRecordSet(OpenstackResource):
    service_type = 'dns'
    resource_type = 'recordset'
    zone_id = ''

    def get(self):
        recordset = self.find_recordset()
        return recordset

    def find_recordset(self, zone_id=None, name_or_id=None):
        if not zone_id:
            zone_id = self.zone_id
        if not name_or_id:
            name_or_id = self.name if not\
                self.resource_id else self.resource_id
        self.logger.debug(
            'Attempting to find this recordset: {0}'.format(name_or_id))
        recordset = self.connection.dns.find_recordset(
            zone_id, name_or_id, ignore_missing=False
        )
        self.logger.debug(
            'Found recordset with this result: {0}'.format(recordset))
        return recordset

    def create(self):
        self.logger.debug(
            'Attempting to create recordset with these args: {0}'.format(
                self.config))
        self.zone_id = self.config.pop('zone_id', None)
        recordset = \
            self.connection.dns.create_recordset(self.zone_id, **self.config)
        self.logger.info(
            'Created recordset with this result: {0}'.format(recordset))
        self.zone_id = recordset['zone_id']
        return recordset

    def delete(self):
        recordset = self.get()
        self.logger.debug(
            'Attempting to delete this recordset: {0}'.format(recordset))
        result = self.connection.dns.delete_recordset(recordset)
        self.logger.debug(
            'Deleted recordset with this result: {0}'.format(result))
        self.zone_id = ''
        return result
