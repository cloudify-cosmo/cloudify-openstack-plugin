[![Build Status](https://circleci.com/gh/cloudify-cosmo/cloudify-openstack-plugin.svg?style=shield&circle-token=:circle-token)](https://circleci.com/gh/cloudify-cosmo/cloudify-openstack-plugin)

# cloudify-openstack-plugin

## Plugin Versions

### Version 2.14.X

Cloudify Openstack Plugin version 2 is the original Cloudify Openstack plugin. It is based on the old Openstack Python Client packages:

  * keystoneauth1
  * python-novaclient
  * python-keystoneclient
  * python-neutronclient
  * python-cinderclient
  * python-glanceclient

These Python API bindings are still maintained.

Cloudify is commited to maintanance-level support for Cloudify Openstack Plugin versions 2.14.X.

Cloudify Openstack Plugin Version 2 is supported from Cloudify 3.4.2+.

### Version 3

Cloudify Openstack Plugin version 3 is the new Cloudify Openstack Plugin. It is based on the [Unified Openstack Python SDK in Python](https://github.com/openstack/openstacksdk).

This is the version of the plugin that will include new features in additional to maintenance changes.

### Version 2 and Version 3 Compatibility

In principle, Openstack Plugin versions 2 and 3 are not compatible. However, there is a `compat.yaml` importable yaml file that can translate some version 2 functionality into version 3. For more information, see [notes on Openstack Plugin v2 and v3 compatibility](https://docs.cloudify.co/5.0.0/working_with/official_plugins/infrastructure/openstackv3/#note-on-openstack-plugin-v2-x-compatibility).

Cloudify Openstack Plugin Version 3 is supported from Cloudify 4.5.5+.
