from os import path, pardir
from ecosystem_cicd_tools.validations import validate_plugin_version

package_dir = path.join(
    path.abspath(
        path.join(path.dirname(__file__), pardir)
    )
)


if __name__ == '__main__':
    validate_plugin_version(package_dir)
