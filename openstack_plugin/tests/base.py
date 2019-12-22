# #######
# Copyright (c) 2018 Cloudify Platform Ltd. All rights reserved
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

# Standard imports
import copy
import uuid
import unittest

# Third party imports
import openstack.identity.v3.project
from cloudify.manager import DirtyTrackingDict
from cloudify.state import current_ctx
from cloudify.mocks import (
    MockCloudifyContext,
    MockNodeContext,
    MockNodeInstanceContext,
    MockRelationshipContext,
    MockRelationshipSubjectContext,
)


class CustomMockCloudifyContext(MockCloudifyContext):
    def __init__(self, *args, **kwargs):
        super(CustomMockCloudifyContext, self).__init__(*args, **kwargs)

    @property
    def workflow_id(self):
        return 'workflow'


class CustomMockNodeContext(MockNodeContext):
    def __init__(self,
                 id=None,
                 properties=None,
                 type=None,
                 type_hierarchy=['cloudify.nodes.Root']):
        super(CustomMockNodeContext, self).__init__(id=id,
                                                    properties=properties)
        self._type = type
        self._type_hierarchy = type_hierarchy

    @property
    def type(self):
        return self._type

    @property
    def type_hierarchy(self):
        return self._type_hierarchy


class OpenStackTestBase(unittest.TestCase):

    def setUp(self):
        super(OpenStackTestBase, self).setUp()

    def tearDown(self):
        current_ctx.clear()
        super(OpenStackTestBase, self).tearDown()

    def _to_DirtyTrackingDict(self, origin):
        if not origin:
            origin = {}
        dirty_dict = DirtyTrackingDict()
        for k in origin:
            dirty_dict[k] = copy.deepcopy(origin[k])
        return dirty_dict

    @property
    def client_config(self):
        return {
            'auth_url': 'foo',
            'username': 'foo',
            'password': 'foo',
            'region_name': 'foo',
            'project_name': 'foo'
        }

    @property
    def resource_config(self):
        return {
            'name': 'foo',
            'description': 'foo'
        }

    @property
    def node_properties(self):
        return {
            'client_config': self.client_config,
            'resource_config': self.resource_config
        }

    @property
    def project_resource(self):
        return openstack.identity.v3.project.Project(**{
            'id': 'a95b5509-c122-4c2f-823e-884bcs2efda6',
            'name': 'test_project',
            'description': 'Testing Project',
            'domain_id': 'test_domain_id',
            'enabled': True,
            'is_domain': True,
            'links': ['test1', 'test2'],
            'parent_id': 'test_parent_id'

        })

    @property
    def runtime_properties(self):
        return {}

    def get_mock_ctx(self,
                     test_name,
                     test_properties={},
                     test_runtime_properties={},
                     test_relationships=None,
                     type_hierarchy=['cloudify.nodes.Root'],
                     node_type='cloudify.nodes.Root',
                     test_source=None,
                     test_target=None,
                     ctx_operation_name=None):

        operation_ctx = {
            'retry_number': 0, 'name': 'cloudify.interfaces.lifecycle.'
        } if not ctx_operation_name else {
            'retry_number': 0, 'name': ctx_operation_name
        }

        prop = copy.deepcopy(test_properties or self.node_properties)
        ctx = CustomMockCloudifyContext(
            node_id=test_name,
            node_name=test_name,
            deployment_id=test_name,
            properties=prop,
            runtime_properties=self._to_DirtyTrackingDict(
                test_runtime_properties or self.runtime_properties
            ),
            source=test_source,
            target=test_target,
            relationships=test_relationships,
            operation=operation_ctx
        )

        ctx._node = CustomMockNodeContext(test_name, prop)
        # In order to set type for the node, we need to set it using _node
        # instance
        ctx._node._type = node_type
        ctx._node._type_hierarchy = type_hierarchy
        return ctx

    def _prepare_context_for_operation(self,
                                       test_name,
                                       test_properties={},
                                       test_runtime_properties={},
                                       test_relationships=None,
                                       type_hierarchy=['cloudify.nodes.Root'],
                                       test_source=None,
                                       test_target=None,
                                       ctx_operation_name=None):
        self._ctx = self.get_mock_ctx(
            test_name=test_name,
            test_properties=test_properties,
            test_runtime_properties=test_runtime_properties,
            test_relationships=test_relationships,
            type_hierarchy=type_hierarchy,
            test_source=test_source,
            test_target=test_target,
            ctx_operation_name=ctx_operation_name)
        current_ctx.set(self._ctx)

    def get_mock_relationship_ctx(self,
                                  deployment_name=None,
                                  node_id=None,
                                  test_properties={},
                                  test_runtime_properties={},
                                  test_source=None,
                                  test_target=None,
                                  ctx_operation=None):

        ctx = CustomMockCloudifyContext(
            node_id=node_id,
            deployment_id=deployment_name,
            properties=copy.deepcopy(test_properties),
            source=test_source,
            target=test_target,
            runtime_properties=copy.deepcopy(test_runtime_properties),
            operation=ctx_operation)
        return ctx

    def get_mock_relationship_ctx_for_node(self, rel_specs):
        """
        This method will generate list of mock relationship associated with
        certain node
        :param rel_specs: Relationships is an ordered collection of
        relationship specs - dicts with the keys "node" and "instance" used
        to construct the MockNodeContext and the MockNodeInstanceContext,
        and optionally a "type" key.
        Examples: [
            {},
            {"node": {"id": 5}},
            {
                "type": "some_type",
                "instance": {
                    "id": 3,
                    "runtime_properties":{}
                }
            }
        ]
        :return list: Return list of "MockRelationshipContext" instances
        """

        relationships = []
        for rel_spec in rel_specs:
            node = rel_spec.get('node', {})
            node_id = node.pop('id', uuid.uuid4().hex)

            instance = rel_spec.get('instance', {})
            instance_id = instance.pop('id', '{0}_{1}'.format(
                node_id, uuid.uuid4().hex))
            if 'properties' not in node:
                node['properties'] = {}

            mock_data = {
                'id': node_id,
                'properties': node['properties'],
            }

            if rel_spec.get('type_hierarchy'):
                mock_data['type_hierarchy'] = rel_spec['type_hierarchy']

            node_ctx = CustomMockNodeContext(**mock_data)
            instance_ctx = MockNodeInstanceContext(id=instance_id, **instance)

            rel_subject_ctx = MockRelationshipSubjectContext(
                node=node_ctx, instance=instance_ctx)
            rel_type = rel_spec.get('type')
            rel_ctx = MockRelationshipContext(target=rel_subject_ctx,
                                              type=rel_type)
            relationships.append(rel_ctx)

        return relationships

    def _pepare_relationship_context_for_operation(self,
                                                   deployment_id,
                                                   source,
                                                   target,
                                                   ctx_operation_name=None,
                                                   node_id=None):

        operation_ctx = {
            'retry_number': 0, 'name': 'cloudify.interfaces.lifecycle.'
        } if not ctx_operation_name else {
            'retry_number': 0, 'name': ctx_operation_name
        }

        self._ctx = self.get_mock_relationship_ctx(
            node_id=node_id,
            deployment_name=deployment_id,
            test_source=source,
            test_target=target,
            ctx_operation=operation_ctx)
        current_ctx.set(self._ctx)
