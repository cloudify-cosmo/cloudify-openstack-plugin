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

from setuptools import setup


setup(
    zip_safe=True,
    name='cloudify-openstack-plugin',
    version='1.2',
    author='idanmo',
    author_email='idan@gigaspaces.com',
    packages=[
        'openstack_plugin_common',
        'nova_plugin',
        'neutron_plugin',
        'cinder_plugin',
        'keystone_plugin',
        'glance_plugin',
    ],
    license='LICENSE',
    description='Cloudify plugin for OpenStack infrastructure.',
    install_requires=[
        'cloudify-plugins-common>=3.2.1',
        'python-novaclient==2.26.0',
        'python-keystoneclient==1.6.0',
        'python-neutronclient==2.6.0',
        'python-cinderclient==1.2.2',
	'python-glanceclient==0.12.0',
        'IPy==0.81'
    ]
)
