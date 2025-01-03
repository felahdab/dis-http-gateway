import os
from twisted.internet import reactor, task
from twisted.internet.defer import inlineCallbacks
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers
import json

from config import load_config_from_env
from dis_receiver import DISReceiver
from dis_emitter import DISEmitter
from pdu_extension import extend_pdu_factory

# Poll API and emit PDUs
@inlineCallbacks
def poll_api(endpoint, token, interval, emitter):
    agent = Agent(reactor)
    while True:
        headers = Headers({
            "Authorization": [f"Bearer {token}"]
        })
        response = yield agent.request(b"GET", endpoint.encode("utf-8"), headers)
        body = yield readBody(response)
        data = json.loads(body)
        print(f"Received API data: {data}")
        if "position" in data and "route" in data and "speed" in data:
            emitter.send_pdu(data["position"], data["route"], data["speed"])
        yield task.deferLater(reactor, interval, lambda: None)


def main():
    # Extend the PDU factory
    extend_pdu_factory()

    # Load configuration from environment variables
    config = load_config_from_env()

    # Initialize DIS receiver
    receiver = DISReceiver(config["http_receiver"], config["http_token_receiver"])
    reactor.listenMulticast(config["receiver"]["port"], receiver, listenMultiple=True)

    # Initialize DIS emitter
    emitter = DISEmitter(config["emitter"])
    task.deferLater(
        reactor,
        0,
        poll_api,
        config["http_poller"],
        config["http_token_poller"],
        config["poll_interval"],
        emitter,
    )

    reactor.run()

if __name__ == "__main__":
    main()
