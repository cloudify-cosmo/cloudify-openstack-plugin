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

import base64

# Local imports
from openstack_plugin.tests.base import OpenStackTestBase
from openstack_plugin.utils import is_userdata_encoded


class UtilsTestCase(OpenStackTestBase):

    def setUp(self):
        super(UtilsTestCase, self).setUp()

    def test_base64_encoding(self):
        encoded_string = base64.b64encode('foo')
        not_encoded_string = 'foo'
        self.assertTrue(is_userdata_encoded(encoded_string))
        self.assertFalse(is_userdata_encoded(not_encoded_string))
