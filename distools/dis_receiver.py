import json

from twisted.internet.protocol import DatagramProtocol

from .pdus.pdu_extension import extend_pdu_factory
from .pdus.transfer_ownership_pdu import TransferOwnershipPdu

# Extend the PduFactory to include custom PDUs
extend_pdu_factory()

from opendis.dis7 import EntityStatePdu
from opendis import PduFactory

def pdu_to_dict(pdu_object):
    """
    Transforme un objet PDU en dictionnaire Python.
    Parcourt récursivement les attributs de l'objet.
    """
    result = {}
    for attribute in dir(pdu_object):
        if not attribute.startswith("_") and not callable(getattr(pdu_object, attribute)):
            value = getattr(pdu_object, attribute)
            if isinstance(value, list):
                # Si c'est une liste, applique la conversion à chaque élément
                result[attribute] = [pdu_to_dict(item) if hasattr(item, "__dict__") else item for item in value]
            elif hasattr(value, "__dict__"):
                # Si c'est un objet complexe, appelle récursivement
                result[attribute] = pdu_to_dict(value)
            else:
                result[attribute] = value
    return result

class DISReceiver(DatagramProtocol):
    def __init__(self, poster):
        self.pdu_factory = PduFactory
        self.poster = poster

    def datagramReceived(self, data, addr):
        try:
            pdu = self.pdu_factory.createPdu(data)
            if pdu:
                print(f"Received PDU from {addr}: {pdu}")
                if self.should_relay_pdu(pdu):
                    pdu_json = pdu_to_dict(pdu)
                    self.poster.post_to_api(pdu_json)
        except Exception as e:
            print(f"Error decoding PDU: {e}")

    def should_relay_pdu(self, pdu):
        """
        Decide whether to relay the PDU.
        """
        # Example: Relay only EntityStatePdu
        return isinstance(pdu, EntityStatePdu)

