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

        if (False): # Code réel à réactiver après tests.
            response = yield agent.request(b"GET", endpoint.encode("utf-8"), headers)
            body = yield readBody(response)
            data = json.loads(body)
        else: # code fictif simulant l'obtention d'une objet à générer depuis l'API REST.
            data = {
                "latitude": "43.0",
                "longitude": "5.0",
                "route" : "230",
                "speed": "12.3"
            }

        print(f"Received API data: {data}")

        if "latitude" in data and "longitude" in data and "route" in data and "speed" in data:
            entity_id = 12345
            entity_type = {"kind": 2, "domain": 6, "country": 71, "category": 1, "subcategory": 1}
            # EntityID: SISO-REF010 page 457/768
            # EntityID = 2.6.71.1.1.1 : MM 38 Exocet
            #            2.6.71.1.1.4 : MM 40 Exocet
            # kind=2
            # domain=6: 
            # country=71: France (SISO-REF010 page 96/768)
            # category=1: Guided (SISO-REF010 page 51/768)
            # subcategory=1

            # Ici, il faut calculer la position et la velocite à partir des latitude, longitude, route et vitesse
            # obtenues depuis l'API.
            position = (10.0, 20.0, 0.0)  # Coordonnées de l'entité
            velocity = (1.0, 0.0, 0.0)  # Vitesse de l'entité
            

            emitter.create_entity_sequence(entity_id, entity_type, position, velocity)
        yield task.deferLater(reactor, interval, lambda: None)


def main():
    # Extend the PDU factory
    extend_pdu_factory()

    # Load configuration from environment variables
    config = load_config_from_env()
    print(json.dumps(config, indent=3))

    # Initialize DIS receiver
    receiver = DISReceiver(config["http_receiver"], config["http_token_receiver"])
    reactor.listenMulticast(config["receiver"]["port"], receiver, listenMultiple=True)

    # Initialize DIS emitter
    emitter = DISEmitter(config)
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
