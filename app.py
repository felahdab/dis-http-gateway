import json

from twisted.web.client import Agent
from twisted.internet import reactor, ssl
from twisted.internet.defer import ensureDeferred
from twisted.web.client import BrowserLikePolicyForHTTPS
from twisted.web.iweb import IPolicyForHTTPS
from urllib.parse import urlparse

from config.config import load_config_from_env
from distools.dis_communicator import DISCommunicator
from distools.pdus.pdu_extension import extend_pdu_factory
from httptools.http_poster import HttpPoster
from httptools.http_poller import HttpPoller
from treq.client import HTTPClient
from zope.interface import implementer

@implementer(IPolicyForHTTPS)
class WhitelistContextFactory:
    def __init__(self, good_domains=None):
        self.good_domains = good_domains or []
        self.default_policy = BrowserLikePolicyForHTTPS()

    def creatorForNetloc(self, hostname, port):
        if hostname in self.good_domains:
            return ssl.CertificateOptions(verify=False)
        return self.default_policy.creatorForNetloc(hostname, port)

def main():
    extend_pdu_factory()
    try:
        config = load_config_from_env()
    except ValueError as e:
        print(f"[ERROR] {e}")
        return
    # print(json.dumps(config, indent=3))
    poller_domain = urlparse(config["http_poller"]).hostname
    ack_domain = urlparse(config["http_ack_endpoint"]).hostname
    whitelist_domains = [d.encode("utf-8") for d in {poller_domain, ack_domain}] # Has to be encoded because Twisted creatorForNetloc takes hostnames as byte arrays
    # Setup treq with custom agent
    agent = Agent(reactor, contextFactory=WhitelistContextFactory(whitelist_domains))
    shared_http_client = HTTPClient(agent)
    
    http_poster = HttpPoster(shared_http_client, config["http_receiver"], config["http_ack_endpoint"],config["http_token_receiver"])

    communicator = DISCommunicator(http_poster, config["receiver"], config["emitter"], config["remote_dis_site"])
    reactor.listenMulticast(config["receiver"]["port"], communicator, listenMultiple=True)

    poller = HttpPoller(
        config["http_poller"],
        config["http_token_poller"],
        config["poll_interval"],
        communicator,
        http_poster,
        config["http_ack_endpoint"],
        config["is_debug_on"],
        shared_http_client
    )
    reactor.callWhenRunning(lambda: ensureDeferred(poller.run()))
    reactor.run()

if __name__ == "__main__":
    main()
