from twisted.application import service

from webproxy426 import backendWebServer, backendTLSWebServer


application = service.Application("A web server running on an IPv6-only host.")
backendWebServer.setServiceParent(application)
backendTLSWebServer.setServiceParent(application)
