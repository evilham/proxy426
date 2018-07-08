from twisted.web import server, resource
from twisted.internet import reactor
from twisted.application import service, strports

from functools import lru_cache

@lru_cache(maxsize=1024)
def check_host(host, acmeService):
    acmeService.check_or_issue_cert(host)
    return True


class BackendWebResource(resource.Resource):
    """
    Simple L{twisted.web.resource.Resource} that shows the hostname
    that was used to query the server.
    This is meant to run on the IPv6-only servers.
    """

    def __init__(self, acmeService=None):
        super(BackendWebResource, self).__init__()
        self.acmeService = acmeService

    def render(self, request):
        host = request.requestHeaders.getRawHeaders(b"Host")[0]

        check_host(host.decode('utf-8'), self.acmeService)

        return host

    def getChild(self, path, request):
        """
        Done like this we don't break static entities, which is needed
        for our implementation of C{.well-known}.
        """
        return self
