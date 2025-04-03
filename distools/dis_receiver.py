import json

from twisted.internet.protocol import DatagramProtocol

from .pdus.pdu_extension import extend_pdu_factory
from .pdus.transfer_ownership_pdu import TransferOwnershipPdu
from .pdus.tools import pdu_to_dict

# Extend the PduFactory to include custom PDUs
extend_pdu_factory()

from opendis.dis7 import EntityStatePdu
from opendis import PduFactory

class DISReceiver(DatagramProtocol):
    def __init__(self, poster, broadcast):
        self.pdu_factory = PduFactory
        self.poster = poster
        print("DISReceiver broadcast: " + str(broadcast))
        self.broadcast = broadcast

    def startProtocol(self):
        if self.broadcast:
            self.transport.setBroadcastAllowed(True)

    def datagramReceived(self, data, addr):
        try:
            pdu = self.pdu_factory.createPdu(data)
            if pdu:
                pdu_json = pdu_to_dict(pdu)
                print(f"Received PDU from {addr}: {pdu_json}")
                if self.should_relay_pdu(pdu):
                    self.poster.post_to_api(pdu_json)
        except Exception as e:
            print(f"Error decoding PDU: {e}")

    def should_relay_pdu(self, pdu):
        """
        Decide whether to relay the PDU.
        """
        # Example: Relay only EntityStatePdu
        return isinstance(pdu, EntityStatePdu)

