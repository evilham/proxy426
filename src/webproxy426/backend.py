from twisted.web import server, resource
from twisted.internet import reactor
from twisted.application import service, strports

class BackendWebResource(resource.Resource):
    """
    Simple L{twisted.web.resource.Resource} that shows the hostname
    that was used to query the server.
    This is meant to run on the IPv6-only servers.
    """

    def render(self, request):
        host = request.requestHeaders.getRawHeaders(b"Host")[0]
        return host

    def getChild(self, path, request):
        """
        Done like this we don't break static entities, which is needed
        for our implementation of C{.well-known}.
        """
        return self
