class HttpPoster:
    def __init__(self, http_client, endpoint_receiver, ack_endpoint, http_token):
        self.http_client = http_client
        self.endpoint_receiver = endpoint_receiver
        self.ack_endpoint = ack_endpoint
        self.http_token = http_token

    async def post_ack_to_api(self, json_payload):
        headers = {
            "User-Agent" : [ f"Mozilla/5.0 (platform; rv:gecko-version) Gecko/gecko-trail Firefox/firefox-version"],
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.http_token}"
        }
        try:
            response = await self.http_client.post(
                self.ack_endpoint,
                headers=headers,
                json=json_payload
            )
            print(f"[HttpPoster] HTTP POST response: {response.code}")
        except Exception as e:
            print(f"[HttpPoster] HTTP POST failed: {e}")
