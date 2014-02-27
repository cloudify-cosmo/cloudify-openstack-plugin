__author__ = 'idanmo'

from setuptools import setup

COSMO_CELERY_VERSION = "0.3"
COSMO_CELERY_BRANCH = "develop"
COSMO_CELERY = "https://github.com/CloudifySource/" \
               "cosmo-celery-common/tarball/{0}".format(COSMO_CELERY_BRANCH)


setup(
    zip_safe=True,
    name='cloudify-openstack-plugin',
    version='0.1.0',
    author='idanmo',
    author_email='idan@gigaspaces.com',
    packages=[
        'openstack_plugin_common',
        'nova_plugin',
        'neutron_plugin'
    ],
    license='LICENSE',
    description='Cloudify plugin for OpenStack infrastructure.',
    install_requires=[
        "cosmo-celery-common",
        "python-novaclient",
        "python-keystoneclient",
        "python-neutronclient"
    ],
    dependency_links=["{0}#egg=cosmo-celery-common-{1}"
                      .format(COSMO_CELERY, COSMO_CELERY_VERSION)]
)
