# Copyright (c) 2017-2019 Cloudify Platform Ltd. All rights reserved
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

import os
import re
import pathlib
import sys
from setuptools import setup, find_packages


def get_version():
    current_dir = pathlib.Path(__file__).parent.resolve()
    with open(os.path.join(current_dir,
                           'openstack_plugin/__version__.py'),
              'r') as outfile:
        var = outfile.read()
        return re.search(r'\d+.\d+.\d+', var).group()


install_requires = [
    'openstacksdk==0.53.0',
    'IPy==0.81',
    'pycryptodome>=3.9.8,<3.10',
    'python-manilaclient==2.0.0'
]

if sys.version_info.major == 3 and sys.version_info.minor == 6:
    install_requires += [
        'cloudify-common>=4.5,<7.0',
        'cloudify-utilities-plugins-sdk>=0.0.91',  # includes YAML
    ]
    packages = [
        'openstack_plugin',
        'openstack_sdk',
        'openstack_plugin.resources',
        'openstack_plugin.resources.compute',
        'openstack_plugin.resources.dns_service',
        'openstack_plugin.resources.identity',
        'openstack_plugin.resources.network',
        'openstack_plugin.resources.share',
        'openstack_plugin.resources.volume',
        'openstack_plugin.tests.dns_service',
        'openstack_sdk.resources',
    ]
else:
    install_requires += [
        'fusion-common',
        'fusion-mgmtworker',
        'cloudify-utilities-plugins-sdk',
    ]
    packages = find_packages(exclude=['tests*'])


setup(
    name='cloudify-openstack-plugin',
    version=get_version(),
    author='Cloudify',
    author_email='info@cloudify.co',
    license='LICENSE',
    zip_safe=False,
    packages=packages,
    install_requires=install_requires,
)