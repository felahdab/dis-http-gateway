class HttpPoster:
    def __init__(self, http_client, endpoint_receiver, ack_endpoint, http_token):
        self.http_client = http_client
        self.endpoint_receiver = endpoint_receiver
        self.ack_endpoint = ack_endpoint
        self.http_token = http_token

    async def post_to_api(self, json_payload, is_ack):
        headers = {
            "User-Agent" : [ f"Mozilla/5.0 (platform; rv:gecko-version) Gecko/gecko-trail Firefox/firefox-version"],
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.http_token}"
        }
        try:
            response = await self.http_client.post(
                self.ack_endpoint if is_ack else self.endpoint_receiver,
                headers=headers,
                json=json_payload
            )
            print(f"[HTTP INFO:{'ACK' if is_ack else 'PDU'}] HTTP POST response: {response.code}")
        except Exception as e:
            print(f"[HTTP INFO:{'ACK' if is_ack else 'PDU'}] HTTP POST failed: {e}")
