from twisted.python.filepath import FilePath
from twisted.application import strports
from twisted.web import server

from webproxy426.vhostresource import DynamicVirtualHostProxy
from webproxy426.management import managementApp
from webproxy426.backend import BackendWebResource
from webproxy426.tls import MagicTLSProtocolFactory, AcmeService

import os

staging = os.environ.get('LE_PRODUCTION', False) == False
managementPort = os.environ.get('PROXY_MANAGEMENT', 8080)
backendHTTP = os.environ.get('PROXY_BACKEND_HTTP', 80)
backendHTTPS = os.environ.get('PROXY_BACKEND_HTTPS', 443)
frontendHTTP = os.environ.get('PROXY_FRONTEND_HTTP', 80)
frontendHTTPS = os.environ.get('PROXY_FRONTEND_HTTPS', 443)
certDir = FilePath(os.environ.get('PROXY_CERT_DIR',
                                  '../acme.certs')).asTextMode()

# Whitelist persistency bits
persistency = FilePath('whitelist')

def restoreVhostResource():
    if persistency.isfile():
        whitelist = persistency.getContent().split(b'\n')
        vhostResource = DynamicVirtualHostProxy(hostWhitelist=set(whitelist))
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

acmeService = AcmeService(staging=staging, pem_path=certDir)

# Restore VirtualHostProxy with whitelist after initialising acmeService
vhostResource = restoreVhostResource()

webProxyServer = strports.service(
    'tcp6:port={}'.format(frontendHTTP),
    server.Site(vhostResource))

webTLSProxyServer = strports.service(
    'tcp6:port={}'.format(frontendHTTPS),
    MagicTLSProtocolFactory(webProxyServer.factory,
                            acmeService=acmeService))

managementServer = strports.service(
    'tcp6:port={}'.format(managementPort),
    server.Site(managementApp(vhostResource, persist).resource()))

backendWebServer = strports.service(
    'tcp6:port={}'.format(backendHTTP),
    server.Site(BackendWebResource(acmeService)))

backendTLSWebServer = strports.service(
    'tcp6:port={}'.format(backendHTTPS),
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
