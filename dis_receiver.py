from twisted.internet.protocol import DatagramProtocol
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.internet import reactor, task

import json
from pdu_extension import extend_pdu_factory
from pdus.transfer_ownership_pdu import TransferOwnershipPdu
from memory_body_producer import MemoryBodyProducer

# Extend the PduFactory to include custom PDUs
extend_pdu_factory()

from opendis.dis7 import EntityStatePdu
from opendis import PduFactory

class DISReceiver(DatagramProtocol):
    def __init__(self, http_endpoint, http_token):
        self.http_endpoint = http_endpoint
        self.http_token = http_token
        self.pdu_factory = PduFactory

    def datagramReceived(self, data, addr):
        try:
            pdu = self.pdu_factory.createPdu(data)
            if pdu:
                print(f"Received PDU from {addr}: {pdu}")
                if self.should_relay_pdu(pdu):
                    pdu_json = pdu.to_dict()
                    self.post_to_api(pdu_json)
        except Exception as e:
            print(f"Error decoding PDU: {e}")

    def should_relay_pdu(self, pdu):
        """
        Decide whether to relay the PDU.
        """
        # Example: Relay only EntityStatePdu
        return isinstance(pdu, EntityStatePdu)

    def post_to_api(self, pdu_json):
        agent = Agent(reactor)
        headers = Headers({
            "Content-Type": ["application/json"],
            "Authorization": [f"Bearer {self.http_token}"]
        })
        body = json.dumps(pdu_json).encode("utf-8")
        agent.request(
            b"POST",
            self.http_endpoint.encode("utf-8"),
            headers,
            MemoryBodyProducer(body),
        ).addCallback(self.handle_response).addErrback(self.handle_error)

    def handle_response(self, response):
        print(f"HTTP POST response: {response.code}")

    def handle_error(self, failure):
        print(f"HTTP POST failed: {failure}")
