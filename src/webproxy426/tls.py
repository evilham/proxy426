from twisted.python.filepath import FilePath
from twisted.internet import defer, reactor
from twisted.protocols.tls import TLSMemoryBIOFactory

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

class MagicTLSProtocolFactory(TLSMemoryBIOFactory):
    def __init__(self,
                 protocolFactory,
                 pem_path=pem_path,
                 acme_key=None,
                 staging=True,
                 sni_map=None):

        _ensure_dirs(pem_path)

        if acme_key is None:
            acme_key = load_or_create_client_key(pem_path)
        self.acme_key = acme_key

        self.cert_store = DirectoryStore(pem_path)
        cert_mapping = HostDirectoryMap(pem_path)

        self.staging = staging
        self.responder = HTTP01Responder # TODO

        if not sni_map:
            sni_map = SNIMap(cert_mapping)

        super(MagicTLSProtocolFactory, self).__init__(
            contextFactory=sni_map,
            isClient=False,
            wrappedFactory=protocolFactory,
        )

    def startFactory(self):
        if self.staging:
            acme_url = txacme.urls.LETSENCRYPT_STAGING_DIRECTORY
        else:
            acme_url = txacme.urls.LETSENCRYPT_DIRECTORY

        self.service = AcmeIssuingService(
            clock=reactor,
            client_creator=partial(Client.from_url,
                                   reactor, acme_url,
                                   key=self.acme_key),
            cert_store=self.cert_store,
            responders=[self.responder],
        )
        self.service.startService()
        super(MagicTLSProtocolFactory, self).startFactory()

    def stopFactory(self):
        self.service.stopService()
        super(MagicTLSProtocolFactory, self).stopFactory()
