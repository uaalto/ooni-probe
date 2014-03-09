# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

from twisted.internet import defer
from twisted.internet.defer import TimeoutError
from twisted.names import client, dns
from twisted.names.client import Resolver

from twisted.names.error import DNSQueryRefusedError

from ooni.utils import log
from ooni.nettest import NetTestCase
from ooni.errors import failureToString

from socket import gaierror


def representAnswer(answer):
    # We store the resource record and the answer payload in a
    # tuple
    return (repr(answer), repr(answer.payload))

class InvalidProtocol(Exception): pass

class DNSAnswer(object):
    def 

class DNSQuery(object):
    protocol = 'UDP'
    timeout = [1]

    def __init__(self, report):
        self.report = report
    
    def _query(self, q, dns_server=None):
        def callback(message):
            answers = []
            name = ''
            for answer in message.answers:
                if answer.type is 12:
                    name = str(answer.payload.name)
                answers.append(representAnswer(answer))
            return name

        def errback(failure):
            failure.trap(gaierror, TimeoutError)
            DNSTest.addToReport(self, query, resolver=dns_server,
                    query_type = 'PTR', failure=failure)
            return None

        resolver = Resolver(servers=[dns_server])
        if self.protocol == 'UDP':
            d = resolver.queryUDP(query, timeout=self.timeout)
        elif self.protocol == 'TCP':
            d = resolver.queryTCP(query, timeout=self.timeout)
        else:
            raise InvalidProtocol
        d.addCallback(callback)
        d.addErrback(errback)
        return d

    def a(self, name, dns_server=None):
        pass

    def aaaa(self, name, dns_server=None):
        pass

    def ptr(self, name, dns_server=None):
        ptr = '.'.join(name.split('.')[::-1]) + '.in-addr.arpa'
        q = [dns.Query(ptr, dns.PTR, dns.IN)]
        self._query(q, dns_server)

    def ns(self, name, dns_server=None):
        pass

    def cname(self, name, dns_server=None):
        pass

    def mx(self, name, dns_server=None):
        pass

    def txt(self, name, dns_server=None):
        pass

    def soa(self, name, dns_server=None):
        pass

class DNSTest(NetTestCase):
    name = "Base DNS Test"
    version = 'df-001-dnst-001'

    requiresRoot = False
    queryTimeout = [1]
    
    def _setUp(self):
        super(DNSTest, self)._setUp()

        self.report['queries'] = []
        self.query = DNSQuery(self.report)
        self.query.timeout = self.queryTimeout
    
    def performPTRLookup(self, address, dns_server):
        """
        Does a reverse DNS lookup on the input ip address

        :address: the IP Address as a dotted quad to do a reverse lookup on.

        :dns_server: is the dns_server that should be used for the lookup as a
                     tuple of ip port (ex. ("127.0.0.1", 53))

        WARNING: using this method is now deprecated.
                 You should use .query instead.
        """
        ptr = '.'.join(address.split('.')[::-1]) + '.in-addr.arpa'
        query = [dns.Query(ptr, dns.PTR, dns.IN)]
        def gotResponse(message):
            log.debug("Lookup successful")
            log.debug(message)
            answers = []
            name = ''
            for answer in message.answers:
                if answer.type is 12:
                    name = str(answer.payload.name)
                answers.append(representAnswer(answer))

            DNSTest.addToReport(self, query, resolver=dns_server,
                    query_type = 'PTR', answers=answers, name=name)
            return name

        def gotError(failure):
            log.err("Failed to perform lookup")
            log.exception(failure)
            failure.trap(gaierror, TimeoutError)
            DNSTest.addToReport(self, query, resolver=dns_server,
                    query_type = 'PTR', failure=failure)
            return None

        resolver = Resolver(servers=[dns_server])
        d = resolver.queryUDP(query, timeout=self.queryTimeout)
        d.addCallback(gotResponse)
        d.addErrback(gotError)
        return d

    def performALookup(self, hostname, dns_server):
        """
        Performs an A lookup and returns an array containg all the dotted quad
        IP addresses in the response.

        :hostname: is the hostname to perform the A lookup on

        :dns_server: is the dns_server that should be used for the lookup as a
                     tuple of ip port (ex. ("127.0.0.1", 53))
        """
        query = [dns.Query(hostname, dns.A, dns.IN)]
        def gotResponse(message):
            addrs = []
            answers = []
            for answer in message.answers:
                if answer.type is 1:
                    addr = answer.payload.dottedQuad()
                    addrs.append(addr)
                answers.append(representAnswer(answer))

            DNSTest.addToReport(self, query, resolver=dns_server, query_type='A',
                    answers=answers, addrs=addrs)
            return addrs

        def gotError(failure):
            failure.trap(gaierror, TimeoutError)
            DNSTest.addToReport(self, query, resolver=dns_server, query_type='A',
                    failure=failure)
            return failure

        resolver = Resolver(servers=[dns_server])
        d = resolver.queryUDP(query, timeout=self.queryTimeout)
        d.addCallback(gotResponse)
        d.addErrback(gotError)
        return d

    def addToReport(self, query, resolver=None, query_type=None,
                    answers=None, name=None, addrs=None, failure=None):
        log.debug("Adding %s to report)" % query)
        result = {}
        result['resolver'] = resolver
        result['query_type'] = query_type
        result['query'] = repr(query)
        result['protocol'] = 'udp'
        if failure:
            result['failure'] = failureToString(failure)

        if answers:
            result['answers'] = answers
            if name:
                result['name'] = name
            if addrs:
                result['addrs'] = addrs

        self.report['queries'].append(result)
