from os import path, pardir
from ecosystem_cicd_tools.release import plugin_release_with_latest
from ecosystem_cicd_tools.validations import get_plugin_yaml_version


plugin_yaml = path.join(
    path.abspath(path.join(path.dirname(__file__), pardir)),
    'plugin.yaml')


if __name__ == '__main__':
    plugin_release_with_latest(
        'cloudify-openstack-plugin', get_plugin_yaml_version(plugin_yaml))
