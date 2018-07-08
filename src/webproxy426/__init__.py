from twisted.python.filepath import FilePath
from twisted.application import strports
from twisted.web import server

from webproxy426.vhostresource import DynamicVirtualHostProxy
from webproxy426.management import managementApp
from webproxy426.backend import BackendWebResource
from webproxy426.tls import MagicTLSProtocolFactory, AcmeService

import os

staging = os.environ.get('LE_PRODUCTION', False) == False

# Whitelist persistency bits
persistency = FilePath('whitelist')

def restoreVhostResource():
    if persistency.isfile():
        whitelist = persistency.getContent().split(b'\n')
        vhostResource = DynamicVirtualHostProxy(hostWhitelist=whitelist)
        # Trigger possible cert checks
        _acme_check_certs(whitelist)
    else:
        vhostResource = DynamicVirtualHostProxy()
    return vhostResource

def persist():
    """
    Save current whitelist to disk as closely to an atomary OP as possible.
    """
    persistency.setContent(b'\n'.join(list(vhostResource.hostWhitelist)))
    persistency.chmod(0o600)
    # Trigger possible cert checks
    _acme_check_certs(vhostResource.hostWhitelist)

# End whitelist persistency bits

def _acme_check_certs(hosts):
    for bhost in hosts:
        host = bhost.decode('utf-8')
        acmeService.check_or_issue_cert(host)

acmeService = AcmeService(staging=staging)

# Restore VirtualHostProxy with whitelist after initialising acmeService
vhostResource = restoreVhostResource()

webProxyServer = strports.service(
    'tcp6:port=80',
    server.Site(vhostResource))

webTLSProxyServer = strports.service(
    'tcp6:port=443',
    MagicTLSProtocolFactory(webProxyServer.factory,
                            acmeService=acmeService))

managementServer = strports.service(
    'tcp6:port=8080',
    server.Site(managementApp(vhostResource, persist).resource()))

backendWebServer = strports.service(
    'tcp6:port=80',
    server.Site(BackendWebResource()))

backendTLSWebServer = strports.service(
    'tcp6:port=443',
    MagicTLSProtocolFactory(backendWebServer.factory,
                            acmeService=acmeService))


__all__ = [
    'acmeService',
    'webProxyServer',
    'webTLSProxyServer',
    'managementServer',
    'backendWebServer',
    'backendTLSWebServer',
]
