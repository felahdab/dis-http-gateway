from twisted.internet import reactor, task
from twisted.internet.protocol import DatagramProtocol

from opendis.DataOutputStream import DataOutputStream
from opendis.dis7 import EntityStatePdu, EntityID, EntityType, Vector3Double, Vector3Float
from io import BytesIO
from twisted.internet.protocol import DatagramProtocol
import random
from enum import IntEnum
from pprint import pprint

from opendis.dis7 import EntityStatePdu
from opendis import PduFactory

class IPTransmissionType(IntEnum):
    UNICAST = 0
    MULTICAST = 1
    BROADCAST = 2

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

ENTITY_TYPE_MAP = {
    (1, 2, 78, 22, 2, 0): "NH90",
    (2, 6, 71, 1, 1, 4): "ExocetMM40",
    (1, 3, 62, 6, 5, 1): "Normandie",
}

def get_entity_name(pdu="Unkown"):
    entity_type = pdu.entityType
    return ENTITY_TYPE_MAP.get((entity_type.entityKind, entity_type.domain, entity_type.country, entity_type.category, entity_type.subcategory, entity_type.specific), "UnknownEntity")

class NH90(EntityType):
    def __init__(self):
        super().__init__(entityKind=1, domain=2, country=78, category=22, subcategory=2, specific=0)

class ExocetMM40(EntityType):
    def __init__(self):
        super().__init__(entityKind=2, domain=6, country=71, category=1, subcategory=1, specific=4)

class Normandie(EntityType):
    def __init__(self):
        super().__init__(entityKind=1, domain=3, country=62, category=6, subcategory=5, specific=1)

class DISCommunicator(DatagramProtocol):
    def __init__(self, send_addr, send_port, recv_addr=None, interval=1.0, mode=IPTransmissionType.BROADCAST):
        self.pdu_factory = PduFactory
        self.send_addr = send_addr
        self.send_port = send_port
        self.recv_addr = recv_addr
        self.interval = interval
        self.mode = mode
        self.loop = None
        self.entity_number = 1

    def startProtocol(self):
        print(f"[INFO] Protocol started")
        if (self.mode == IPTransmissionType.MULTICAST):
            self.transport.joinGroup(self.recv_addr)
            print(f"[INFO] Joined multicast group {self.recv_addr}")
        elif (self.mode == IPTransmissionType.BROADCAST):
            self.transport.setBroadcastAllowed(True)
            self.send_addr = "<broadcast>"
    
        self.loop = task.LoopingCall(self.send_pdu)
        self.loop.start(self.interval)

    def datagramReceived(self, data, addr):
        try:
            pdu = self.pdu_factory.createPdu(data)
            if pdu:
                pdu_json = pdu_to_dict(pdu)
                EID = pdu.entityID
                print(f"[RECV] {get_entity_name(pdu):<10} Entity with SN={EID.siteID:<2}, AN={EID.applicationID:<3}, EN={EID.entityID:<3} from {addr[0]}")
                # pprint(pdu_json)
        except Exception as e:
            print(f"Error decoding PDU: {e}")

    def send_pdu(self):
        pdu = self.build_entity_state_pdu()
        memoryStream = BytesIO()
        outputStream = DataOutputStream(memoryStream)
        pdu.serialize(outputStream)
        data = memoryStream.getvalue()
        self.transport.write(data, (self.send_addr, self.send_port))
        EID = pdu.entityID
        print(f"[SEND] {get_entity_name(pdu):<10} Entity with SN={EID.siteID:<2}, AN={EID.applicationID:<3}, EN={EID.entityID:<3} sent to {self.send_addr}:{self.send_port}")

    def build_entity_state_pdu(self):
        pdu = EntityStatePdu()
        pdu.pduStatus = 0
        pdu.entityAppearance = 0
        pdu.capabilities = 0
        pdu.pduType = 1 
        pdu.exerciseID = 1
        pdu.protocolFamily = 1
        pdu.length = 144
        pdu.pduStatus = 6
        pdu.entityID = EntityID( # Simulate red team Excon instance: send unique entity ID from one of red team's 3 units 
            siteID=20,                                     # 10 = Blue, 20 = Red
            applicationID=random.choice([100, 200, 300]),  # 100 = Unit1, 200 = Unit2, 300 = Unit3
            entityID=self.entity_number
        )
        pdu.entityType = random.choice([ExocetMM40, NH90, Normandie])()
        pdu.entityLocation = Vector3Double(x=1000.0, y=2000.0, z=300.0)
        pdu.entityLinearVelocity = Vector3Float(x=0.0, y=0.0, z=0.0)
        pdu.entityAppearance = 0
        pdu.marking.characterSet = 1  # ASCII [UID 45]
        pdu.marking.setString("MISSILE")
        self.entity_number += 1
        return pdu

def main():
    communicator = DISCommunicator(send_addr="228.0.0.5", send_port=3000, recv_addr="229.0.0.5", interval=3.0, mode=IPTransmissionType.BROADCAST)
    
    reactor.listenMulticast(3001, communicator, listenMultiple=True)
    reactor.run()

if __name__ == "__main__":
    main()