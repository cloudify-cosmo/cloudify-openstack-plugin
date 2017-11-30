########
# Copyright (c) 2017 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import unittest

from mock import patch

import neutron_plugin.router
from cloudify.mocks import MockCloudifyContext
from cloudify.state import current_ctx

from openstack_plugin_common import (NeutronClientWithSugar,
                                     OPENSTACK_ID_PROPERTY)
from cloudify.exceptions import NonRecoverableError


@patch('openstack_plugin_common.NeutronClientWithSugar')
class TestRouter(unittest.TestCase):

    def test_update_router(self, mock_nc):
        args = {'router': {}}
        node_props = {}
        ctx = self._get_mock_ctx_with_node_properties(node_props)
        current_ctx.set(ctx=ctx)

        neutron_plugin.router.update(
            neutron_client=mock_nc, args=args)

    def test_update_router_wrong_type(self, mock_nc):
        args = {'router': {'routes': ''}}
        node_props = {}
        ctx = self._get_mock_ctx_with_node_properties(node_props)
        current_ctx.set(ctx=ctx)
        with self.assertRaises(NonRecoverableError):
            neutron_plugin.router.update(
                neutron_client=mock_nc, args=args)

    @staticmethod
    def _get_mock_ctx_with_node_properties(properties):
        return MockCloudifyContext(
            node_id='test_node_id',
            properties=properties,
            runtime_properties={OPENSTACK_ID_PROPERTY: 'id'})


class MockNeutronClient(NeutronClientWithSugar):
    """A fake neutron client with hard-coded test data."""
    def __init__(self, update):
        self.update = update
        self.body = {'router_id': '', 'router': {'routes': []}}

    def show_router(self, *_):
        return self.body

    def update_router(self, _, b, **__):
        if self.update:
            self.body.update(b)
        return
