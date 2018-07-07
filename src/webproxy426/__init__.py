from twisted.python.filepath import FilePath
from twisted.application import strports
from twisted.web import server

from webproxy426.vhostresource import DynamicVirtualHostProxy
from webproxy426.management import managementApp
from webproxy426.backend import BackendWebResource
from webproxy426.tls import MagicTLSProtocolFactory

# Whitelist persistency bits
persistency = FilePath('whitelist')

if persistency.isfile():
    vhostResource = DynamicVirtualHostProxy(
        hostWhitelist=persistency.getContent().split(b'\n'))
else:
    vhostResource = DynamicVirtualHostProxy()

def persist():
    """
    Save current whitelist to disk as closely to an atomary OP as possible.
    """
    persistency.setContent(b'\n'.join(list(vhostResource.hostWhitelist)))
    persistency.chmod(0o600)
# End whitelist persistency bits


webProxyServer = strports.service(
    'tcp6:port=80',
    server.Site(vhostResource))

webTLSProxyServer = strports.service(
    'tcp6:port=443',
    MagicTLSProtocolFactory(webProxyServer))

managementServer = strports.service(
    'tcp6:port=8080',
    server.Site(managementApp(vhostResource, persist).resource()))

backendWebServer = strports.service(
    'tcp6:port=80',
    server.Site(BackendWebResource()))

backendTLSWebServer = strports.service(
    'tcp6:port=443',
    MagicTLSProtocolFactory(backendWebServer))


__all__ = [
    'webProxyServer',
    'webTLSProxyServer',
    'managementServer',
    'backendWebServer',
    'backendTLSWebServer',
]
