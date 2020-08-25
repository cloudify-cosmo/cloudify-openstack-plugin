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
from setuptools import setup


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version(rel_file):
    lines = read(rel_file)
    for line in lines.splitlines():
        if 'package_version' in line:
            split_line = line.split(':')
            line_no_space = split_line[-1].replace(' ', '')
            line_no_quotes = line_no_space.replace('\'', '')
            return line_no_quotes.strip('\n')
    raise RuntimeError('Unable to find version string.')


setup(
    zip_safe=True,
    name='cloudify-openstack-plugin',
    version='2.14.20',
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
        'cloudify-common>=4.6',
        'keystoneauth1>=2.16.0,<3',
        'python-novaclient==7.0.0',
        'python-keystoneclient==3.5.0',
        'python-neutronclient==6.0.0',
        'python-cinderclient==1.9.0',
        'python-glanceclient==2.5.0',
        'IPy==0.81'
    ]
)
