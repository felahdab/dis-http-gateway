import os
from twisted.internet import reactor, task
from twisted.internet.defer import inlineCallbacks
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers
from twisted.internet.ssl import ClientContextFactory

import json

from config.config import load_config_from_env
from distools.dis_receiver import DISReceiver
from distools.dis_emitter import DISEmitter
from distools.pdus.pdu_extension import extend_pdu_factory
from distools.geotools.tools import natural_velocity_to_ECEF

from simtools.objects import Missile

from httptools.http_poster import HttpPoster

from opendis.RangeCoordinates import GPS, deg2rad, rad2deg
from opendis.dis7 import EntityID

gps = GPS()

class WebClientContextFactory(ClientContextFactory):
    def getContext(self, hostname, port):
        return ClientContextFactory.getContext(self)
    

# Poll API and emit PDUs
@inlineCallbacks
def poll_api(endpoint, token, ignorecertificate, interval, emitter, ackendpoint, is_debug_on):
    if ignorecertificate:
        contextFactory = WebClientContextFactory()
        agent = Agent(reactor, contextFactory)
    else:
        agent = Agent(reactor)
    http_poster = HttpPoster(ackendpoint, token, ignorecertificate)

    while True:
        headers = Headers({
            "User-Agent" : [ f"Mozilla/5.0 (platform; rv:gecko-version) Gecko/gecko-trail Firefox/firefox-version"],
            "Authorization": [f"Bearer {token}"]
        })
        if (is_debug_on): # code fictif simulant l'obtention d'un objet à générer depuis l'API REST.
            data = [{
                "id": 4,
                "timestamp": "2025-04-17T00:00:00.000000Z",
                "latitude": 43.0,
                "longitude": 5.0,
                "target_latitude": 44,
                "target_longitude": 5,
                "AN": 1,
                "EN": 22,
                "entity_type" : {"kind": 2, "domain": 6, "country": 71, "category": 1, "subcategory": 1, "specific": 4, "extra": 0},
                "speed": 318,
                "course" : 230,
                "maxrange" : 10,
            }]
        else: # Code réel à réactiver après tests.
            response = yield agent.request(b"GET", endpoint.encode("utf-8"), headers)
            body = yield readBody(response)
            data = json.loads(body)
            print(body)

        print(f"Received API data: {data}")

        for enga in data:
            if "latitude" in enga and "longitude" in enga and "course" in enga and "speed" in enga:
                entity_type = enga["entity_type"]
                # EntityType: SISO-REF010 page 457/768
                # EntityType = 2.6.71.1.1.1 : MM 38 Exocet
                #            2.6.71.1.1.4 : MM 40 Exocet
                # kind=2
                # domain=6: 
                # country=71: France (SISO-REF010 page 96/768)
                # category=1: Guided (SISO-REF010 page 51/768)
                # subcategory=1

                # Inputs:
                # lat   : latitude of the entity in radians
                # lon   : longitude of the entity in radians
                # alt   : altitude of the entity in meters
                # roll  : roll of the entity in radians
                # pitch : pitch of the entity in radians
                # yaw   : yaw (heading) of the entity in radians

                lat = enga["latitude"]
                lon = enga["longitude"]
                alt = 5
                initial_position =[lat, lon, alt]
                entity_id = EntityID(emitter.get_RemoteDISSite(), enga["AN"], enga["EN"])
                missile = Missile(entity_id, entity_type, emitter, initial_position, enga["course"], enga["speed"], enga["maxrange"])
                loop = task.LoopingCall(missile.update)
                missile.setLoop(loop)
                loopDefered = loop.start(5.0)
                if "id" in enga:
                    http_poster.post_to_api({"engagement" : enga["id"]})
        yield task.deferLater(reactor, interval, lambda: None)

def main():
    # Extend the PDU factory
    extend_pdu_factory()

    # Load configuration from environment variables
    config = load_config_from_env()
    print(json.dumps(config, indent=3))

    # Initialize the HTTP poster
    http_poster = HttpPoster(config["http_receiver"], config["http_token_receiver"], config["http_ignore_cert"])
    # Initialize DIS receiver
    broadcast = config["receiver"]["mode"] == "broadcast"
    receiver = DISReceiver(http_poster, broadcast)
    reactor.listenMulticast(config["receiver"]["port"], receiver, listenMultiple=True)

    # Initialize DIS emitter
    emitter = DISEmitter(config)
    task.deferLater(
        reactor,
        0,
        poll_api,
        config["http_poller"],
        config["http_token_poller"],
        config["http_ignore_cert"],
        config["poll_interval"],
        emitter,
        config["http_ack_endpoint"],
        config["is_debug_on"]
    )

    reactor.run()

if __name__ == "__main__":
    main()
