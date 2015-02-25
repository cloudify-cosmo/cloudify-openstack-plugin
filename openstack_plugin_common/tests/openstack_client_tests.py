########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
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

import os
import unittest
import tempfile
import json

from mock import MagicMock

import openstack_plugin_common as common


class OpenstackClientsTests(unittest.TestCase):

    def test_clients_custom_configuration(self):
        # tests for clients custom configuration, passed via properties/inputs

        envars_cfg = {
            'OS_USERNAME': 'envar-username',
            'OS_PASSWORD': 'envar-password',
            'OS_TENANT_NAME': 'envar-tenant-name',
            'OS_AUTH_URL': 'envar-auth-url'
        }

        # file config passes custom_configuration too, but it'll get overridden
        # by the inputs custom_configuration
        file_cfg = {
            'username': 'file-username',
            'password': 'file-password',
            'tenant_name': 'file-tenant-name',
            'custom_configuration': {
                'nova_client': {'username': 'custom-username',
                                'api_key': 'custom-password',
                                'project_id': 'custom-tenant-name'},
            }
        }

        inputs_cfg = {
            'username': 'inputs-username',
            'custom_configuration': {
                'neutron_client': {'password': 'inputs-custom-password'},
                'cinder_client': {'api_key': 'inputs-custom-password',
                                  'auth_url': 'inputs-custom-auth-url',
                                  'extra_key': 'extra-value'},
                'keystone_client': {'username': 'inputs-custom-username',
                                    'tenant_name': 'inputs-custom-tenant-name'}
            }
        }

        nova_params, neut_params, cind_params, keys_params = \
            self._create_clients(envars_cfg, file_cfg, inputs_cfg)

        # the first three assertions also check inputs custom-configuration
        # completely overrides file custom-configuration
        self.assertEquals('inputs-username', nova_params['username'])
        self.assertEquals('file-password', nova_params['api_key'])
        self.assertEquals('file-tenant-name', nova_params['project_id'])
        self.assertEquals('envar-auth-url', nova_params['auth_url'])

        self.assertEquals('inputs-username', neut_params['username'])
        self.assertEquals('inputs-custom-password', neut_params['password'])
        self.assertEquals('file-tenant-name', neut_params['tenant_name'])
        self.assertEquals('envar-auth-url', neut_params['auth_url'])

        self.assertEquals('inputs-username', cind_params['username'])
        self.assertEquals('inputs-custom-password', cind_params['api_key'])
        self.assertEquals('file-tenant-name', cind_params['project_id'])
        self.assertEquals('inputs-custom-auth-url', cind_params['auth_url'])
        self.assertEquals('extra-value', cind_params['extra_key'])

        self.assertEquals('inputs-custom-username', keys_params['username'])
        self.assertEquals('file-password', keys_params['password'])
        self.assertEquals('inputs-custom-tenant-name',
                          keys_params['tenant_name'])
        self.assertEquals('envar-auth-url', keys_params['auth_url'])

    def test_clients_custom_configuration_from_file(self):
        # tests for clients custom configuration loaded from file

        envars_cfg = {
            'OS_USERNAME': 'envar-username',
            'OS_PASSWORD': 'envar-password',
            'OS_TENANT_NAME': 'envar-tenant-name',
            'OS_AUTH_URL': 'envar-auth-url'
        }

        file_cfg = {
            'username': 'file-username',
            'password': 'file-password',
            'tenant_name': 'file-tenant-name',
            'custom_configuration': {
                'nova_client': {'project_id': 'inputs-custom-tenant-name'},
                'neutron_client': {'password': 'inputs-custom-password'},
                'cinder_client': {'api_key': 'inputs-custom-password',
                                  'auth_url': 'inputs-custom-auth-url',
                                  'extra_key': 'extra-value'},
                'keystone_client': {'username': 'inputs-custom-username'}
            }
        }

        inputs_cfg = {
            'username': 'inputs-username'
        }

        nova_params, neut_params, cind_params, keys_params = \
            self._create_clients(envars_cfg, file_cfg, inputs_cfg)

        self.assertEquals('inputs-username', nova_params['username'])
        self.assertEquals('file-password', nova_params['api_key'])
        self.assertEquals('inputs-custom-tenant-name',
                          nova_params['project_id'])
        self.assertEquals('envar-auth-url', nova_params['auth_url'])

        self.assertEquals('inputs-username', neut_params['username'])
        self.assertEquals('inputs-custom-password', neut_params['password'])
        self.assertEquals('file-tenant-name', neut_params['tenant_name'])
        self.assertEquals('envar-auth-url', neut_params['auth_url'])

        self.assertEquals('inputs-username', cind_params['username'])
        self.assertEquals('inputs-custom-password', cind_params['api_key'])
        self.assertEquals('file-tenant-name', cind_params['project_id'])
        self.assertEquals('inputs-custom-auth-url', cind_params['auth_url'])
        self.assertEquals('extra-value', cind_params['extra_key'])

        self.assertEquals('inputs-custom-username', keys_params['username'])
        self.assertEquals('file-password', keys_params['password'])
        self.assertEquals('file-tenant-name', keys_params['tenant_name'])
        self.assertEquals('envar-auth-url', keys_params['auth_url'])

    def _create_clients(self, envars_cfg, file_cfg, inputs_cfg):
        client_init_args = []

        def client_mock(**kwargs):
            client_init_args.append(kwargs)
            return MagicMock()

        orig_nova_client = common.NovaClientWithSugar
        orig_neut_client = common.NeutronClientWithSugar
        orig_cind_client = common.CinderClientWithSugar
        orig_keys_client = common.keystone_client.Client

        try:
            common.NovaClientWithSugar = client_mock
            common.NeutronClientWithSugar = client_mock
            common.CinderClientWithSugar = client_mock
            common.keystone_client.Client = client_mock

            # envars config
            os.environ.update(envars_cfg)

            # file config
            conf_file_path = tempfile.mkstemp()[1]
            os.environ[common.Config.OPENSTACK_CONFIG_PATH_ENV_VAR] = \
                conf_file_path
            with open(conf_file_path, 'w') as f:
                json.dump(file_cfg, f)

            common.NovaClient().get(config=inputs_cfg)
            common.NeutronClient().get(config=inputs_cfg)
            common.CinderClient().get(config=inputs_cfg)
            common.KeystoneClient().get(config=inputs_cfg)

            return client_init_args  # nova, neut, cind, keys
        finally:
            common.NovaClientWithSugar = orig_nova_client
            common.NeutronClientWithSugar = orig_neut_client
            common.CinderClientWithSugar = orig_cind_client
            common.keystone_client.Client = orig_keys_client
