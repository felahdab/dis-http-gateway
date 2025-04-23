
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
        while True:
            try:
                print("=============================================================")
                data = await self.fetch_data()
                await self.process_engagements(data)
            except Exception as e:
                print(f"[HTTP POLL ERROR] {e}")
            await task.deferLater(reactor, self.interval, lambda: None)

    async def fetch_data(self):
        if self.is_debug_on:
            return [{
                "id": 4,
                "timestamp": "2025-04-17T00:00:00.000000Z",
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
                "maxrange": 10
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
        self.created_missiles = { # Remove missiles that reached their max range
            entity_id: missile
            for entity_id, missile in self.created_missiles.items()
            if not missile.is_out_of_range
        }
        for enga in data:
            if all(k in enga for k in ("latitude", "longitude", "course", "speed")):
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
                        enga["maxrange"]
                    )
                    self.created_missiles[entity_id] = missile
                    loop = task.LoopingCall(missile.update)
                    missile.setLoop(loop)
                    loop.start(5.0)
                    if "EN" in enga:
                        await self.http_poster.post_to_api({"engagement" : enga["EN"]}, is_ack=True)