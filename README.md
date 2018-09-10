# Serve IPv6 services over IPv4 proxies

Developed at #Hack4Glarus summer 2018.

https://hack4glarus.ch

https://evilham.com/en/slides/2018-Hack4Glarus-summer


## Background

Check article (in German):
https://www.pro-linux.de/artikel/2/1938/warum-sie-ipv6-brauchen.html

> UPDATE: This may be a complete overkill and a terrible idea :-D.
> Apparently Nginx has Proxying abilities for mail protocols.
> https://docs.nginx.com/nginx/admin-guide/mail-proxy/mail-proxy/

## Implementation

This uses Twisted Python extensively.
Check https://twistedmatrix.com

## Status
The proxy/frontend is currently usable, the backend is just for testing and
should never be used.

This uses a custom `AcmeService` that issues or renews TLS certificates
on the fly for allowed domains.

It is pretty much zero-config, in that it queries DNS for the AAAA records
of the counter party IPv6 host.

## TODO
* Check if acme challenges are served if queried via IP.

## Running

    # If using pipenv
    pipenv sync
    # Otherwise make some virtual environment and run
    pip install -r requirements.txt
    # Run this on the dual stack server that will proxy IPv4 requests:
    twistd -ny proxy.py
    # Run this on the IPv6-only servers
    twistd -ny backend.py

## Configuring

Use environment variables:

    managementPort = os.environ.get('PROXY_MANAGEMENT', 8080)
    backendHTTP = os.environ.get('PROXY_BACKEND_HTTP', 80)
    backendHTTPS = os.environ.get('PROXY_BACKEND_HTTPS', 443)
    frontendHTTP = os.environ.get('PROXY_FRONTEND_HTTP', 80)
    frontendHTTPS = os.environ.get('PROXY_FRONTEND_HTTPS', 443)
    certDir = FilePath(os.environ.get('PROXY_CERT_DIR',
                                      '../acme.certs')).asTextMode()

## Management API
There is a very basic management API that is evil (tm) and has no
auth{entication,orisation} mechanisms whatsoever.
See `./src/webproxy426/management.py`.

## Roadmap

- [X] HTTP
- [X] HTTPS
- [ ] SMTP
- [ ] SMTPS
- [ ] IMAP
- [ ] IMAPS
- [ ] SIP?
