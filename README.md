cloudify-openstack-plugin
=========================

[![Circle CI](https://circleci.com/gh/cloudify-cosmo/cloudify-openstack-plugin/tree/master.svg?style=shield)](https://circleci.com/gh/cloudify-cosmo/cloudify-openstack-plugin/tree/master)
[![Build Status](https://travis-ci.org/cloudify-cosmo/cloudify-openstack-plugin.svg?branch=master)](https://travis-ci.org/cloudify-cosmo/cloudify-openstack-plugin)

Cloudify OpenStack Plugin

## Usage

See [Openstack Plugin](https://docs.cloudify.co/latest/developer/official_plugins/openstack/)


## Known Issues

You may experience such an error when using a local profile:

```shell
ERROR:cloudify.cli.main:(PyYAML 3.10 (/.../python2.7/site-packages), Requirement.parse('PyYAML>=3.12'), set(['oslo.config']))
```

Cloudify CLI requires PyYAML 3.10, whereas Openstack Python SDK Libraries require PyYAML 3.12. For this reason, if you wish to use Cloudify Openstack Plugin in a local profile, you will need to upgrade the PyYAML 3.12 in your virtualenv.

Fix:

```shell
pip install -U pyyaml==3.12
```

At this stage, you should no longer use the flag `--install-plugins` with the `cfy` CLI.
