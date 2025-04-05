from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.internet import reactor, task
from twisted.internet.ssl import ClientContextFactory
import json
from .memory_body_producer import MemoryBodyProducer

class WebClientContextFactory(ClientContextFactory):
    def getContext(self, hostname, port):
        return ClientContextFactory.getContext(self)
    

class HttpPoster:
    def __init__(self, http_endpoint, http_token, ignore_certificate):
        self.http_endpoint = http_endpoint
        self.http_token = http_token
        self.ignore_certificate = ignore_certificate
        if ignore_certificate:
            contextFactory = WebClientContextFactory()
            self.agent = Agent(reactor, contextFactory)
        else:
            self.agent = Agent(reactor)

    def post_to_api(self, jsondumpable):
        agent = self.agent
        headers = Headers({
            "Content-Type": ["application/json"],
            "Authorization": [f"Bearer {self.http_token}"]
        })
        body = json.dumps(jsondumpable, indent=4)
        #print(body)
        
        agent.request(
            b"POST",
            self.http_endpoint.encode("utf-8"),
            headers,
            MemoryBodyProducer(body.encode("utf-8")),
        ).addCallback(self.handle_response).addErrback(self.handle_error)

    def handle_response(self, response):
        print(f"HTTP POST response: {response.code}")

    def handle_error(self, failure):
        print(f"HTTP POST failed: {failure}")