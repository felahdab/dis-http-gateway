
from twisted.internet import reactor, task
from twisted.internet import reactor
from twisted.web import http

from simtools.objects import Missile
from opendis.dis7 import EntityID

class HttpPoller:
    def __init__(self, endpoint, token, interval, emitter, http_poster, ack_endpoint, is_debug_on, http_client):
        self.endpoint = endpoint
        self.token = token
        self.interval = interval
        self.emitter = emitter
        self.http_poster = http_poster
        self.ack_endpoint = ack_endpoint
        self.is_debug_on = is_debug_on
        self.created_missiles = dict()
        self.http_client = http_client

    async def run(self):
        """
        Runs the HTTP poller loop.
        Fetches data from the configured HTTP endpoint and process the engagements, with a configured interval between each. 
        """
        while True:
            try:
                print("=============================================================")
                data = await self.fetch_data()
                await self.process_engagements(data)
            except Exception as e:
                print(f"[HTTP POLL ERROR] {e}")
            await task.deferLater(reactor, self.interval, lambda: None)

    async def fetch_data(self):
        """
        Polls engagement data from API.
        If debug mode is activated, use dummy data.
        
        Returns:
            a list of JSON dictionnaries of one or more engagements
        """
        if self.is_debug_on:
            return [{
                "id": 4,
                "latitude": 43.0,
                "longitude": 5.0,
                "target_latitude": 44,
                "target_longitude": 5,
                "AN": 1,
                "EN": 22,
                "entity_type": {
                    "kind": 2, "domain": 6, "country": 71,
                    "category": 1, "subcategory": 1,
                    "specific": 4, "extra": 0
                },
                "speed": 318,
                "course": 230,
                "maxrange": 10,
                "current_time": 1747084972, # Endpoint timestamp (UTC)
                "timestamp": 1747084949,    # Engagement timestamp
                "weapon_flight_time": 125.78616352201257 # Maximum flight time
            }]
        else:
            response = await self.http_client.get(self.endpoint, headers={
                "User-Agent" : [ f"Mozilla/5.0 (platform; rv:gecko-version) Gecko/gecko-trail Firefox/firefox-version"],
                "Authorization": f"Bearer {self.token}"
            })
            if response.code == http.OK:
                print(f"[HTTP POLL] Polled engagement from {self.endpoint}")
                return await response.json()
            else:
                # message = await response.text() # full error
                # raise Exception(f"Got an error from the server: {message}")
                raise Exception(f"Got an error from the server: {response.code}")

    async def process_engagements(self, data):
        """
        Creates a missile from each polled engagement and POST an ack to the HTTP endpoint
        
        Args:
            data: a list of JSON dictionnaries of one or more engagements
        """
        self.created_missiles = { # Remove missiles that reached their max range
            entity_id: missile
            for entity_id, missile in self.created_missiles.items()
            if not missile.is_out_of_range
        }
        for enga in data:
            if all(k in enga for k in ("latitude", "longitude", "course", "speed")):
                print(f"[HTTP POLL] Valid engagement data received.")
                entity_type = enga["entity_type"]
                lat, lon, alt = enga["latitude"], enga["longitude"], 5
                entity_id = (self.emitter.get_RemoteDISSite(), enga["AN"], enga["EN"])
                if entity_id not in self.created_missiles:
                    missile = Missile(
                        EntityID(self.emitter.get_RemoteDISSite(), enga["AN"], enga["EN"]),
                        entity_type,
                        self.emitter,
                        [lat, lon, alt],
                        enga["course"],
                        enga["speed"],
                        enga["maxrange"],
                        enga["timestamp"],
                        enga["current_time"],
                        enga["weapon_flight_time"]
                    )
                    if missile.is_out_of_range is True:
                        print("[HTTP POLL] Received engagement (EN {0}) is out of range already. Acknowleding it without sending a DIS EntityStatePDU.".format(enga["EN"]))
                    else:
                        self.created_missiles[entity_id] = missile
                        loop = task.LoopingCall(missile.update)
                        missile.setLoop(loop)
                        loop.start(5.0)
                    if "EN" in enga:
                        print("[HTTP POLL] Acknowledging EN {0}".format(enga["EN"]))
                        await self.http_poster.post_to_api({"engagement" : enga["EN"]}, is_ack=True)