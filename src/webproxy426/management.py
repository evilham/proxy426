"""
Very basic VHost Whitelist Management API.
Has no auth, depends on network isolation.
"""
from klein import Klein
import json

def managementApp(vhostResource, persist):
    """
    Return a management API Klein app.

    @param vhostResource: The VirtualHost proxy to be managed.
    @type  vhostResource: L{webproxy426.vhostresource.DynamicVirtualHostProxy}

    @param persist: A function that will be called on changes to the whitelist.
    @type  persist: Callable that takes no arguments.
    """
    app = Klein()

    @app.route('/add')
    def addToWhitelist(request):
        """
        API point to add hosts.
        Pass as many instances of C{host} as C{GET} or C{POST} arguments.
        """
        hosts = request.args.get(b'host', [])
        for host in hosts:
            if host not in vhostResource.hostWhitelist:
                vhostResource.hostWhitelist.add(host)
        persist()
        return "OK"

    @app.route('/remove')
    def removeFromWhitelist(request):
        """
        API point to remove hosts.
        Pass as many instances of C{host} as C{GET} or C{POST} arguments.
        """
        hosts = set(request.args.get(b'host', []))
        vhostResource.hostWhitelist = vhostResource.hostWhitelist.difference(
            hosts)
        persist()
        return "OK"

    @app.route('/list')
    def showWhitelist(request):
        """
        Return a list of all whitelisted C{host} elements.
        Does not include any hosts that are whitelisted through a function.
        Does not support parameters.
        """
        return json.dumps([
            host.decode('utf-8') for host in vhostResource.hostWhitelist
        ])

    @app.route('/check')
    def checkHosts(request):
        """
        Check if a set of hosts is valid.
        This checks both the whitelist and the validation function.
        Returns a C{JsonObject} whose keys are the hosts
        and values are C{True} or C{False}.
        """
        hosts = set(request.args.get(b'host', []))
        return json.dumps({
            host.decode('utf-8'): vhostResource.isValidHost(host)
            for host in hosts
        })

    return app
