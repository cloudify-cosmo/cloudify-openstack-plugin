########
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


from setuptools import setup
from setuptools import find_packages


setup(
    name='cloudify-openstack-plugin',
    version='3.2.12',
    author='Cloudify',
    author_email='info@cloudify.co',
    license='LICENSE',
    zip_safe=False,
    packages=find_packages(exclude=['tests*']),
    install_requires=['cloudify-common==5.1.0.dev1',
                      'openstacksdk==0.39.0',
                      'IPy==0.81',
                      'pycrypto==2.6.1'],
    test_requires=['mock', 'requests-mock'])
