# Serve IPv6 services over IPv4 proxies

Developed at #Hack4Glarus summer 2018.


## Background

Check article (in German):
https://www.pro-linux.de/artikel/2/1938/warum-sie-ipv6-brauchen.html


## Implementation

This uses Twisted Python extensively.
Check https://twistedmatrix.com


## Running

    # Make some virtual environment
    pip install -r requirements.txt
    # Run this on the dual stack server that will proxy IPv4 requests:
    twistd -ny proxy.py
    # Run this on the IPv6-only servers
    twistd -ny backend.py


## Roadmap

[X] HTTP
[ ] HTTPS
[ ] SMTP
[ ] SMTPS
[ ] IMAP
[ ] IMAPS
[ ] SIP?
