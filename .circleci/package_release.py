from os import path, pardir
from ecosystem_cicd_tools.release import (
    plugin_release, find_version)

setup_py = path.join(
    path.abspath(path.join(path.dirname(__file__), pardir)),
    'setup.py')


if __name__ == '__main__':
    plugin_release(
        'cloudify-openstack-plugin', find_version(setup_py))
