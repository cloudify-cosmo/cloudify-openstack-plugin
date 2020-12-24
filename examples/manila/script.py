# For development help:
from manilaclient import client
# Fill in with real values.
manila = client.Client(
    client_version='2',
    username='admin',
    password='openstack',
    project_name='demo',
    auth_url='http://10.11.12.2/identity',
    user_domain_name='Default',
    project_domain_name='default')
share_networks = manila.share_networks.list()
shares = manila.shares.list()
