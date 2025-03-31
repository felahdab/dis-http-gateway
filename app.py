import os
from twisted.internet import reactor, task
from twisted.internet.defer import inlineCallbacks
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers
import json

from config.config import load_config_from_env
from distools.dis_receiver import DISReceiver
from distools.dis_emitter import DISEmitter
from distools.pdus.pdu_extension import extend_pdu_factory
from distools.geotools.tools import natural_velocity_to_ECEF

from httptools.http_poster import HttpPoster

from opendis.RangeCoordinates import GPS, deg2rad, rad2deg

gps = GPS()

# Poll API and emit PDUs
@inlineCallbacks
def poll_api(endpoint, token, interval, emitter):
    agent = Agent(reactor)
    while True:
        headers = Headers({
            "Authorization": [f"Bearer {token}"]
        })

        if (True): # Code réel à réactiver après tests.
            response = yield agent.request(b"GET", endpoint.encode("utf-8"), headers)
            body = yield readBody(response)
            data = json.loads(body)
            print(body)
        else: # code fictif simulant l'obtention d'un objet à générer depuis l'API REST.
            data = {
                "latitude": 43.0,
                "longitude": 5.0,
                "course" : 230,
                "speed": 12.3,
                "entity_type" : {"kind": 2, "domain": 6, "country": 71, "category": 1, "subcategory": 1}
            }

        print(f"Received API data: {data}")

        for enga in data:
            if "latitude" in enga and "longitude" in enga and "course" in enga and "speed" in enga:
                print("handling data")
                entity_id = 12345
                entity_type = enga["entity_type"]
                # EntityID: SISO-REF010 page 457/768
                # EntityID = 2.6.71.1.1.1 : MM 38 Exocet
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

                # """
                # Convert lat, lon, alt to Earth-centered, Earth-fixed coordinates.
                # Input: lla - (lat, lon, alt) in (decimal degrees, decimal degees, m)
                # Output: ecef - (x, y, z) in (m, m, m)
                # """
                (X, Y, Z) = gps.lla2ecef( [lat, lon, alt])
                (Xvel, Yvel, Zvel) = natural_velocity_to_ECEF(lat, lon, alt, enga["course"], enga["speed"])


                position = (X, Y, Z)  # Coordonnées de l'entité
                velocity = (Xvel, Yvel, Zvel)  # Vitesse de l'entité

                #emitter.create_entity_sequence(entity_id, entity_type, position, velocity)
                emitter.emit_entity_state(entity_id, entity_type, position, velocity)

        yield task.deferLater(reactor, interval, lambda: None)

def main():
    # Extend the PDU factory
    extend_pdu_factory()

    # Load configuration from environment variables
    config = load_config_from_env()
    print(json.dumps(config, indent=3))

    # Initialize the HTTP poster
    http_poster = HttpPoster(config["http_receiver"], config["http_token_receiver"])
    # Initialize DIS receiver
    receiver = DISReceiver(http_poster)
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
