from twisted.application import service

from webproxy426 import webProxyServer, webTLSProxyServer, managementServer


application = service.Application("Very Awesome Hack4Glarus IPv4 to IPv6 proxy")

# Do attach the web proxy and management servers to the application
webProxyServer.setServiceParent(application)
webTLSProxyServer.setServiceParent(application)

managementServer.setServiceParent(application)
