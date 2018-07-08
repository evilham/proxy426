from twisted.web import server, proxy, vhost, resource
from twisted.internet import reactor, defer
from twisted.names.client import lookupIPV6Address
from twisted.python.compat import urllib_parse

import socket

# Ugly but works :-D
@defer.inlineCallbacks
def implReverseProxyRenderKeepHost(self, request):
    """
    Actual resource rendering.

    Query C{DNS} for the host's C{AAAA} record. Use the host's IPv6 address
    to establish the TCP connection, but keep the hostname as value of the
    C{Host} HTTP header.
    """
    dns_result = yield lookupIPV6Address(self.host)
    ipv6 = socket.inet_ntop(socket.AF_INET6, dns_result[0][0].payload.address)
    self.host = ipv6
    request.content.seek(0, 0)
    qs = urllib_parse.urlparse(request.uri)[4]
    if qs:
        rest = self.path + b'?' + qs
    else:
        rest = self.path
    clientFactory = self.proxyClientFactoryClass(
        request.method, rest, request.clientproto,
        request.getAllHeaders(), request.content.read(), request)
    self.reactor.connectTCP(self.host, self.port, clientFactory)

def reverseProxyRenderKeepHost(self, request):
    """
    This is needed because the L{twisted.web.resource.Resource.render} method
    is expected to return immediately and therefore cannot use functions with
    L{twisted.internet.defer.Deferred} objects.
    """
    self._render(request)
    return server.NOT_DONE_YET

proxy.ReverseProxyResource._render = implReverseProxyRenderKeepHost
proxy.ReverseProxyResource.render = reverseProxyRenderKeepHost
# End of awesomely ugly hack

class DynamicVirtualHostProxy(vhost.NameVirtualHost):
    """
    A DynamicVirtualHostProxy supporting a whitelist and a validation function.

    @ivar hostWhitelist: This instance's whitelist.
    @ivar validateHostFunc: This instance's validation function.
    """
    def __init__(self, *args, **kwargs):
        """
        Create a DynamicVirtualHostProxy.

        @param hostWhitelist: A set of hosts to whitelist from the beginning.
            Defaults to being empty at start.
        @type  hostWhitelist: L{set}

        @param validateHostFunc: A validation function to apply to the hostname
            after checking the whitelist. Whitelist has priority over this.
        @type  validateHostFunc: Callable accepting C{host} as a parameter.
        """
        self.hostWhitelist = kwargs.pop('hostWhitelist', set())
        self.validateHostFunc = kwargs.pop('validateHostFunc', lambda x: False)
        super(DynamicVirtualHostProxy, self).__init__(*args, **kwargs)

    def _getResourceForRequest(self, request):
        """
        Return the resource matching the C{Host} header in C{request}.

        If host is valid, return matching proxy to C{AAAA} DNS entry.
        If host is not valid, return a C{NoResource} instance.
        """
        if (request.prepath and
            request.prepath[0] in self.listStaticNames()):
            return self.getStaticEntity(request.prepath[0])
        host = request.getHeader(b'host')
        if not self.isValidHost(host):
            return resource.NoResource()
        # Get reverse proxy resource
        return proxy.ReverseProxyResource(host, 80, b'')

    def isValidHost(self, host):
        """
        Check C{Host} header against a whitelist and with a custom function.

        @param host: Host to be checked
        @type  host: L{bytes}
        """
        validHost = host in self.hostWhitelist
        if not validHost:
            validHost = self.validateHost(host)
        return validHost

    def validateHost(self, host):
        """
        Function to check hosts against.

        @param host: Host to be checked
        @type  host: L{bytes}
        """
        return self.validateHostFunc(host)
