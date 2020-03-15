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

import logging

# Runtime properties keys
RESOURCE_ID = 'id'
OPENSTACK_TYPE_PROPERTY = 'type'
OPENSTACK_NAME_PROPERTY = 'name'
OPENSTACK_EXTERNAL_RESOURCE = 'external_resource'
OPENSTACK_AZ_PROPERTY = 'availability_zone'
USE_EXTERNAL_RESOURCE_PROPERTY = 'use_external_resource'
CREATE_IF_MISSING_PROPERTY = 'create_if_missing'
CONDITIONALLY_CREATED = 'conditionally_created'
USE_COMPACT_NODE = 'use_compact_node'
SERVER_TASK_CREATE = 'create_server_task'
SERVER_TASK_STOP = 'stop_server_task'
SERVER_TASK_DELETE = 'delete_server_task'
SERVER_TASK_START = 'start_server_task'
SERVER_TASK_STATE = 'task_state'
SERVER_TASK_BACKUP_DONE = 'backup_done'
SERVER_TASK_RESTORE_STATE = 'restore_state'
SERVER_INTERFACE_IDS = 'interfaces'
VOLUME_TASK_DELETE = 'delete_volume_task'
VOLUME_ATTACHMENT_TASK = 'attach_volume_task'
VOLUME_DETACHMENT_TASK = 'detach_volume_task'
VOLUME_BACKUP_TASK = 'backup_volume_task'
VOLUME_SNAPSHOT_TASK = 'snapshot_volume_task'
VOLUME_SNAPSHOT_ID = 'snapshot_id'
VOLUME_BACKUP_ID = 'backup_id'
VOLUME_ATTACHMENT_ID = 'attachment_id'

# Openstack Server status constants.
# Full lists here: https://bit.ly/2UyB5V5 # NOQA
SERVER_STATUS_ACTIVE = 'ACTIVE'
SERVER_STATUS_BUILD = 'BUILD'
SERVER_STATUS_SHUTOFF = 'SHUTOFF'
SERVER_STATUS_SUSPENDED = 'SUSPENDED'
SERVER_STATUS_ERROR = 'ERROR'
SERVER_STATUS_REBOOT = 'REBOOT'
SERVER_STATUS_HARD_REBOOT = 'HARD_REBOOT'
SERVER_STATUS_UNKNOWN = 'UNKNOWN'

# Openstack volume attachment status constants
VOLUME_STATUS_CREATING = 'creating'
VOLUME_STATUS_DELETING = 'deleting'
VOLUME_STATUS_AVAILABLE = 'available'
VOLUME_STATUS_IN_USE = 'in-use'
VOLUME_STATUS_ERROR = 'error'
VOLUME_STATUS_ERROR_DELETING = 'error_deleting'
VOLUME_ERROR_STATUSES = (VOLUME_STATUS_ERROR, VOLUME_STATUS_ERROR_DELETING)

# Openstack Server reboot actions
SERVER_REBOOT_SOFT = 'SOFT'
SERVER_REBOOT_HARD = 'HARD'

# Openstack resources types
SERVER_OPENSTACK_TYPE = 'server'
SERVER_GROUP_OPENSTACK_TYPE = 'server_group'
INSTANCE_OPENSTACK_TYPE = 'instance'
HOST_AGGREGATE_OPENSTACK_TYPE = 'aggregate'
IMAGE_OPENSTACK_TYPE = 'image'
FLAVOR_OPENSTACK_TYPE = 'flavor'
KEYPAIR_OPENSTACK_TYPE = 'key_pair'
USER_OPENSTACK_TYPE = 'user'
PROJECT_OPENSTACK_TYPE = 'project'
NETWORK_OPENSTACK_TYPE = 'network'
SUBNET_OPENSTACK_TYPE = 'subnet'
ROUTER_OPENSTACK_TYPE = 'router'
PORT_OPENSTACK_TYPE = 'port'
FLOATING_IP_OPENSTACK_TYPE = 'floatingip'
SECURITY_GROUP_OPENSTACK_TYPE = 'security_group'
SECURITY_GROUP_RULE_OPENSTACK_TYPE = 'security_group_rule'
RBAC_POLICY_OPENSTACK_TYPE = 'rbac_policy'
QOS_POLICY_OPENSTACK_TYPE = 'policy'
VOLUME_OPENSTACK_TYPE = 'volume'
VOLUME_BACKUP_OPENSTACK_TYPE = 'backup'
VOLUME_SNAPSHOT_OPENSTACK_TYPE = 'snapshot'
VOLUME_TYPE_OPENSTACK_TYPE = 'type'

# Openstack Image status
IMAGE_UPLOADING = 'image_uploading'
IMAGE_UPLOADING_PENDING = 'image_pending_upload'
IMAGE_STATUS_ACTIVE = 'active'

# Cloudify node types
SERVER_GROUP_NODE_TYPE = 'cloudify.nodes.openstack.ServerGroup'
KEYPAIR_NODE_TYPE = 'cloudify.nodes.openstack.KeyPair'
IMAGE_NODE_TYPE = 'cloudify.nodes.openstack.Image'
NETWORK_NODE_TYPE = 'cloudify.nodes.openstack.Network'
PORT_NODE_TYPE = 'cloudify.nodes.openstack.Port'
SUBNET_NODE_TYPE = 'cloudify.nodes.openstack.Subnet'
VOLUME_NODE_TYPE = 'cloudify.nodes.openstack.Volume'
SECURITY_GROUP_NODE_TYPE = 'cloudify.nodes.openstack.SecurityGroup'

# Cloudify relationship types
RBAC_POLICY_RELATIONSHIP_TYPE = \
    'cloudify.relationships.openstack.rbac_policy_applied_to'


# Message constants
QUOTA_VALID_MSG = \
    'OK: {0} (node {1}) can be created. provisioned {2}: {3}, quota: {4}'

QUOTA_INVALID_MSG = \
    '{0} (node {1}) cannot be created due to quota limitations.' \
    'provisioned {2}: {3}, quota: {4}'

# General constants
OPENSTACK_RESOURCE_UUID = 'uuid'
OPENSTACK_PORT_ID = 'port_id'
OPENSTACK_NETWORK_ID = 'net_id'
PS_OPEN = '<powershell>'
PS_CLOSE = '</powershell>'
INFINITE_RESOURCE_QUOTA = -1
SERVER_ACTION_STATUS_DONE = 'DONE'
SERVER_ACTION_STATUS_PENDING = 'PENDING'
SERVER_REBUILD_STATUS = 'rebuild_done'
SERVER_REBUILD_SPAWNING_STATUS = 'rebuild_spawning'
SERVER_ADMIN_PASSWORD = 'password'
IDENTITY_USERS = 'users'
IDENTITY_ROLES = 'roles'
IDENTITY_QUOTA = 'quota'
VOLUME_BOOTABLE = 'bootable'
VOLUME_DEVICE_NAME_PROPERTY = 'device_name'
CLOUDIFY_CREATE_OPERATION = 'cloudify.interfaces.lifecycle.create'
CLOUDIFY_UPDATE_OPERATION = 'cloudify.interfaces.operations.update'
CLOUDIFY_UPDATE_PROJECT_OPERATION = 'cloudify.interfaces' \
                                    '.operations.update_project'
CLOUDIFY_LIST_OPERATION = 'cloudify.interfaces.operations.list'
CLOUDIFY_CONFIGURE_OPERATION = 'cloudify.interfaces.lifecycle.configure'
CLOUDIFY_START_OPERATION = 'cloudify.interfaces.lifecycle.start'
CLOUDIFY_STOP_OPERATION = 'cloudify.interfaces.lifecycle.stop'
CLOUDIFY_UNLINK_OPERATION = 'cloudify.interfaces.relationship_lifecycle.unlink'
CLOUDIFY_DELETE_OPERATION = 'cloudify.interfaces.lifecycle.delete'
CLOUDIFY_CREATE_VALIDATION = 'cloudify.interfaces.validation.creation'
CLOUDIFY_NEW_NODE_OPERATIONS = [CLOUDIFY_CREATE_OPERATION,
                                CLOUDIFY_CONFIGURE_OPERATION,
                                CLOUDIFY_START_OPERATION,
                                CLOUDIFY_STOP_OPERATION,
                                CLOUDIFY_DELETE_OPERATION,
                                CLOUDIFY_CREATE_VALIDATION]
SERVER_PUBLIC_IP_PROPERTY = 'public_ip'
SERVER_IP_PROPERTY = 'ip'

KEY_USE_CFY_LOGGER = 'use_cfy_logger'
KEY_GROUPS = 'groups'
KEY_LOGGERS = 'loggers'

DEFAULT_LOGGING_CONFIG = {
    KEY_USE_CFY_LOGGER: True,
    KEY_GROUPS: {
        'openstack': logging.DEBUG,
    },
    KEY_LOGGERS: {
    }
}
# Openstack doc https://docs.openstack.org/openstacksdk/
# latest/user/guides/logging.html#python-logging
LOGGING_GROUPS = {
    'openstack': [
        'openstack',
        'openstack.config',
        'openstack.iterate_timeout',
        'openstack.fnmatch',
    ]
}
