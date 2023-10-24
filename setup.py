#########
# Copyright (c) 2018 GigaSpaces Technologies Ltd. All rights reserved
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

import os
import re
import pathlib

from setuptools import setup
from setuptools import find_packages

VERSION_FILE = 'openstack_plugin_common/__version__.py'


def get_version():
    current_dir = pathlib.Path(__file__).parent.resolve()
    with open(os.path.join(current_dir, VERSION_FILE), 'r') as outfile:
        var = outfile.read()
        return re.search(r'\d+.\d+.\d+', var).group()


setup(
    zip_safe=True,
    name='cloudify-openstack-plugin',
    version=get_version(),
    author='Cloudify',
    author_email='hello@cloudify.co',
    packages=[
        'openstack_plugin_common',
        'nova_plugin',
        'neutron_plugin',
        'cinder_plugin',
        'glance_plugin',
        'keystone_plugin'
    ],
    license='LICENSE',
    description='Cloudify plugin for OpenStack infrastructure.',
    install_requires=[
        'cloudify-common>=4.6,<7.0.0',
        'keystoneauth1>=2.16.0,<3',
        'python-novaclient==7.0.0',
        'python-keystoneclient==3.5.0',
        'python-neutronclient==6.0.0',
        'python-cinderclient==1.9.0',
        'python-glanceclient==2.5.0',
        'IPy==0.81'
    ]
)
