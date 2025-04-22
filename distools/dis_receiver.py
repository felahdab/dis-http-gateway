from twisted.internet.protocol import DatagramProtocol

from .pdus.pdu_extension import extend_pdu_factory
from .pdus.transfer_ownership_pdu import TransferOwnershipPdu
from .pdus.tools import pdu_to_dict
from enum import IntEnum
from pprint import pprint
from opendis.dis7 import EntityStatePdu
from opendis import PduFactory

# Extend the PduFactory to include custom PDUs
extend_pdu_factory()

class IPTransmissionType(IntEnum):
    UNICAST = 0
    MULTICAST = 1
    BROADCAST = 2
    
class DISReceiver(DatagramProtocol):
    def __init__(self, poster, ip, mode):
        self.pdu_factory = PduFactory
        self.poster = poster
        self.ip = ip
        self.mode = IPTransmissionType(mode)
        print(f"DISReceiver initialized in {self.mode.name}")

    def startProtocol(self):
        if (self.mode == IPTransmissionType.MULTICAST):
            self.transport.joinGroup(self.ip)
            print(f"[INFO] Joined multicast group {self.ip}")
        elif (self.mode == IPTransmissionType.BROADCAST):
            self.transport.setBroadcastAllowed(True)

    def datagramReceived(self, data, addr):
        try:
            print(f"[RECV] From {addr}: {data[:16]}...")
            pdu = self.pdu_factory.createPdu(data)
            if pdu:
                pdu_json = pdu_to_dict(pdu)
                print(f"Received PDU from {addr}:")
                pprint(pdu_json)
                # if self.should_relay_pdu(pdu):
                    # self.poster.post_to_api(pdu_json)
        except Exception as e:
            print(f"Error decoding PDU: {e}")

    def should_relay_pdu(self, pdu):
        """
        Decide whether to relay the PDU.
        """
        # Example: Relay only EntityStatePdu
        return isinstance(pdu, EntityStatePdu)

