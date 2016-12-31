.. cloudify-cli documentation master file, created by
   sphinx-quickstart on Thu Jun 12 15:30:03 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

cloudify-openstack-plugin documentation
=======================================

The OpenStack plugin allows users to use an OpenStack based cloud infrastructure for deploying services and applications.
For more information about OpenStack, please refer to: https://www.openstack.org/.


Contents:

.. toctree::
    :maxdepth: 2

    configuration
    types
    nova-net
    examples
    tips
    operations


Plugin Requirements
-------------------

* Python versions:
  * 2.7.x
* If the plugin is installed from source,
  then the following system dependencies are required:

  * ``gcc``
  * ``gcc-c++``
  * ``python-devel``


Compatibility
-------------

* *Mitaka* official support*
* *Liberty* official support*
* *Kilo* official support
* *Juno*, *Icehouse* previously supported, not currently tested.

\* support on Mitaka and Liberty currently requires the Keystone URL in [Openstack Configuration](#openstack-configuration) to be explicitly set to `/v2.0`: eg `http://192.0.2.200:5000/v2.0` instead of just `http://192.0.2.200:5000`.

The Openstack plugin uses various Openstack clients packages. The versions used in Openstack Plugin are as follows:

* `Nova client <https://github.com/openstack/python-novaclient>`_ - 2.29.0
* `Neutron client <https://github.com/openstack/python-neutronclient>`_ - 2.6.0
* `Cinder client <https://github.com/openstack/python-cinderclient>`_ - 1.2.2
* `Keystone client <https://github.com/openstack/python-keystoneclient>`_ - 1.6.0




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

