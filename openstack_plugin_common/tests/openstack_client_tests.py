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

import mock
from cloudify.exceptions import NonRecoverableError

from cloudify.mocks import MockCloudifyContext
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

    def test_input_config_override(self):

        def perform_test(ctx, openstack_args, key, expected):
            class ClientClassMock(common.OpenStackClient):
                result_config = None

                def get(self, config, **kwargs):
                    ClientClassMock.result_config = config
                    return mock.MagicMock()

            kwargs = {'ctx': ctx}
            if openstack_args:
                kwargs['openstack_config'] = openstack_args
            common._put_client_in_kw('mock_client', ClientClassMock, kwargs)
            self.assertEquals(expected,
                              ClientClassMock.result_config.get(key, None))

        node_context = MockCloudifyContext(node_id='a20846', properties={})

        perform_test(node_context, {'ignored_prop': 'ignored-prop'},
                     'prop', None)
        perform_test(node_context, {'prop': 'input-property'},
                     'prop', 'input-property')

        node_context = MockCloudifyContext(node_id='a20847',
                                           properties={
                                               'openstack_config': {
                                                   'prop': 'context-property'
                                               }
                                           }
                                           )
        perform_test(node_context, None, 'prop', 'context-property')
        perform_test(node_context, {'prop': 'input-property'},
                     'prop', 'input-property')

        # Making sure that _put_client_in_kw will not modify
        # 'openstack_config' property of a node.
        self.assertEquals('context-property',
                          node_context.node.properties.get(
                              'openstack_config').get('prop'))

    def _create_clients(self, envars_cfg, file_cfg, inputs_cfg):
        client_init_args = []

        def client_mock(**kwargs):
            client_init_args.append(kwargs)
            return mock.MagicMock()

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


class ResourceQuotaTests(unittest.TestCase):

    def _test_quota_validation(self, amount, quota, failure_expected):
        ctx = MockCloudifyContext(node_id='node_id', properties={})
        client = mock.MagicMock()

        def mock_cosmo_list(_):
            return [x for x in range(0, amount)]
        client.cosmo_list = mock_cosmo_list

        def mock_get_quota(_):
            return quota
        client.get_quota = mock_get_quota

        if failure_expected:
            self.assertRaisesRegexp(
                NonRecoverableError,
                'cannot be created due to quota limitations',
                common.validate_resource,
                ctx=ctx, sugared_client=client,
                openstack_type='openstack_type')
        else:
            common.validate_resource(
                ctx=ctx, sugared_client=client,
                openstack_type='openstack_type')

    def test_equals_quotas(self):
        self._test_quota_validation(3, 3, True)

    def test_exceeded_quota(self):
        self._test_quota_validation(5, 3, True)

    def test_infinite_quota(self):
        self._test_quota_validation(5, -1, False)


class UseExternalResourceTests(unittest.TestCase):

    def _test_use_external_resource(self,
                                    is_external,
                                    create_if_missing,
                                    exists):
        properties = {'create_if_missing': create_if_missing,
                      'use_external_resource': is_external,
                      'resource_id': 'resource_id'}
        client_mock = mock.MagicMock()
        os_type = 'test'

        def _raise_error(*_):
            raise NonRecoverableError('Error')

        def _return_something(*_):
            return mock.MagicMock()

        return_value = _return_something if exists else _raise_error
        if exists:
            properties.update({'resource_id': 'rid'})

        node_context = MockCloudifyContext(node_id='a20847',
                                           properties=properties)
        with mock.patch(
                'openstack_plugin_common._get_resource_by_name_or_id_from_ctx',
                new=return_value):
            return common.use_external_resource(node_context,
                                                client_mock, os_type)

    def test_use_existing_resource(self):
        self.assertIsNotNone(self._test_use_external_resource(True, True,
                                                              True))
        self.assertIsNotNone(self._test_use_external_resource(True, False,
                                                              True))

    def test_create_resource(self):
        self.assertIsNone(self._test_use_external_resource(False, True, False))
        self.assertIsNone(self._test_use_external_resource(False, False,
                                                           False))
        self.assertIsNone(self._test_use_external_resource(True, True, False))

    def test_raise_error(self):
        # If exists and shouldn't it is checked in resource
        # validation so below scenario is not tested here
        self.assertRaises(NonRecoverableError,
                          self._test_use_external_resource,
                          is_external=True,
                          create_if_missing=False,
                          exists=False)


class ValidateResourceTests(unittest.TestCase):

    def _test_validate_resource(self,
                                is_external,
                                create_if_missing,
                                exists,
                                client_mock_provided=None):
        properties = {'create_if_missing': create_if_missing,
                      'use_external_resource': is_external,
                      'resource_id': 'resource_id'}
        client_mock = client_mock_provided or mock.MagicMock()
        os_type = 'test'

        def _raise_error(*_):
            raise NonRecoverableError('Error')

        def _return_something(*_):
            return mock.MagicMock()
        return_value = _return_something if exists else _raise_error
        if exists:
            properties.update({'resource_id': 'rid'})

        node_context = MockCloudifyContext(node_id='a20847',
                                           properties=properties)
        with mock.patch(
                'openstack_plugin_common._get_resource_by_name_or_id_from_ctx',
                new=return_value):
            return common.validate_resource(node_context, client_mock, os_type)

    def test_use_existing_resource(self):
        self._test_validate_resource(True, True, True)
        self._test_validate_resource(True, False, True)

    def test_create_resource(self):
        client_mock = mock.MagicMock()
        client_mock.cosmo_list.return_value = ['a', 'b', 'c']
        client_mock.get_quota.return_value = 5
        self._test_validate_resource(False, True, False, client_mock)
        self._test_validate_resource(False, False, False, client_mock)
        self._test_validate_resource(True, True, False, client_mock)

    def test_raise_error(self):
        # If exists and shouldn't it is checked in resource
        # validation so below scenario is not tested here
        self.assertRaises(NonRecoverableError,
                          self._test_validate_resource,
                          is_external=True,
                          create_if_missing=False,
                          exists=False)

    def test_raise_quota_error(self):
        client_mock = mock.MagicMock()
        client_mock.cosmo_list.return_value = ['a', 'b', 'c']
        client_mock.get_quota.return_value = 3
        self.assertRaises(NonRecoverableError,
                          self._test_validate_resource,
                          is_external=True,
                          create_if_missing=True,
                          exists=False,
                          client_mock_provided=client_mock)
