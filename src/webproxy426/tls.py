from twisted.python.filepath import FilePath
from twisted.internet import defer, reactor
from twisted.protocols.tls import TLSMemoryBIOFactory
from twisted.web import server, proxy
from twisted.web.resource import Resource

from txacme.service import AcmeIssuingService
from txacme.store import DirectoryStore
from txacme.endpoint import AutoTLSEndpoint, load_or_create_client_key
from txacme.client import Client
from txacme.challenges import HTTP01Responder

import txacme.urls

from txsni.snimap import SNIMap, HostDirectoryMap

from functools import partial

pem_path = FilePath('acme.certs').asTextMode()

def _ensure_dirs(pem_path=pem_path):
    pem_path.makedirs(ignoreExistingDirectory=True)


class StaticOrReverseProxyResource(Resource):
    def getChild(self, path, request):
        if not request.requestHeaders.hasHeader(b'x-forwarded-for'):
            host = request.getHeader(b'host')
            return proxy.ReverseProxyResource(host, request.getHost().port,
                                              request.path)


class HTTP01ResponderWithProxy(HTTP01Responder):
    def __init__(self):
        self.resource = StaticOrReverseProxyResource()

class MagicTLSProtocolFactory(TLSMemoryBIOFactory):
    def __init__(self,
                 protocolFactory,
                 pem_path=pem_path,
                 acme_key=None,
                 staging=True,
                 sni_map=None,
                 acmeService=None):

        _ensure_dirs(pem_path)

        self.acme_key = acme_key

        cert_mapping = HostDirectoryMap(pem_path)

        self.staging = staging

        if acmeService is None:
            self.acmeService = AcmeService(pem_path=pem_path,
                                           acme_key=acme_key,
                                           staging=staging)
        else:
            self.acmeService = acmeService

        self.responder = self.acmeService._responder

        if isinstance(protocolFactory, server.Site):
            # Add .well-known
            well_known = Resource()
            well_known.putChild(b'acme-challenge', self.responder.resource)
            protocolFactory.resource.putChild(b'.well-known', well_known)


        if not sni_map:
            sni_map = SNIMap(cert_mapping)

        super(MagicTLSProtocolFactory, self).__init__(
            contextFactory=sni_map,
            isClient=False,
            wrappedFactory=protocolFactory,
        )

    def startFactory(self):
        self.acmeService._factories.add(self)
        if not self.acmeService.running:
            self.acmeService.startService()
        super(MagicTLSProtocolFactory, self).startFactory()

    def stopFactory(self):
        self.acmeService._factories.remove(self)
        # Only stop AcmeService if there are no associated factories left
        if self.acmeService.running and not self.acmeService._factories:
            self.acmeService.stopService()
        super(MagicTLSProtocolFactory, self).stopFactory()

class AcmeService(AcmeIssuingService):
    def __init__(self,
                 acme_key=None,
                 staging=True, pem_path=pem_path,
                 clock=reactor, responder=None):
        if responder is None:
            responder = HTTP01ResponderWithProxy()
        # Keep an easy reference to this responder
        self._responder = responder

        if acme_key is None:
            _ensure_dirs(pem_path)
            acme_key = load_or_create_client_key(pem_path)

        if staging:
            acme_url = txacme.urls.LETSENCRYPT_STAGING_DIRECTORY
        else:
            acme_url = txacme.urls.LETSENCRYPT_DIRECTORY

        # Keep track of factories used with this AcmeService
        self._factories = set()

        super(AcmeService, self).__init__(
            clock=clock,
            client_creator=partial(Client.from_url,
                                   reactor=clock, url=acme_url,
                                   key=acme_key),
            cert_store=DirectoryStore(pem_path),
            responders=[responder],
        )

    @defer.inlineCallbacks
    def check_or_issue_cert(self, server_name):
        try:
            yield self.cert_store.get(server_name)
            if self.running:
                self._check_certs()
        except KeyError:
            self.issue_cert(server_name)
