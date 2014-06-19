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

import unittest

from cloudify.mocks import MockCloudifyContext
import nova_plugin.server


class ResourcesRenamingTest(unittest.TestCase):

    def test_resources_renaming(self):
        pfx = 'my_pfx_'
        ctx = MockCloudifyContext(
            node_id='__cloudify_id_server_001',
            properties={
                'server': {
                    'name': 'server_name',
                    'image': '75ce19cd-7ca4-4884-9c2c-f0608bf71e48',  # rand
                    'flavor': '01c44910-6a9d-4c12-b826-e3ca82fcf2f3',  # rand
                    'key_name': 'key_name',
                },
                'management_network_name': 'mg_net_name',
            }
        )
        ### CONTINUE HERE ### nova_plugin.server.start(ctx)

if __name__ == '__main__':
    unittest.main()
