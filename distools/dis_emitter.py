from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor, defer

from opendis.dis7 import (
    EntityStatePdu,
    CreateEntityPdu,
    AcknowledgePdu,
    DataPdu,
    SetDataPdu,
    VariableDatum,
    DatumSpecification
)
from opendis import PduFactory
from opendis.RangeCoordinates import *
from opendis.DataOutputStream import DataOutputStream

from .datums.entity_datums import *
from .pdus.tools import pdu_to_dict

from io import BytesIO
import json
import struct
from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_BROADCAST, SO_REUSEADDR
import os

class DISEmitter(DatagramProtocol):
    def __init__(self, config):
        """
        Initialize the DIS emitter with configuration details.

        :param config: A dictionary containing configuration for the emitter.
        """
        self.config = config
        self.pending_requests = {}  # Store Deferreds for pending requests
        self.socket = socket(AF_INET, SOCK_DGRAM)  # Create a UDP socket
        self.requestID = 1029 # Utilisé uniquement dans le cas d'une séquence de PDU nécessitant un ACK.

        # Set the socket options (e.g., broadcast or multicast)
        if self.config["emitter"]["mode"] == "broadcast":
            print("Broadcast mode selected.")
            self.socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        elif self.config["emitter"]["mode"] == "multicast":
            print("Multicast mode selected.")
            self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.socket.bind((self.config["ip"], self.config["port"]))

    def get_requestID(self):
        ret = self.requestID
        self.requestID = self.requestID + 1
        return ret

    def send_pdu(self, pdu):
        """
        Encode and send a PDU over the network.
        """
        memoryStream = BytesIO()
        outputStream = DataOutputStream(memoryStream)
        pdu.serialize(outputStream)
        data = memoryStream.getvalue()
        destination = (self.config["emitter"]["ip"], self.config["emitter"]["port"])

        self.socket.sendto(data, destination)
        print(f"Sent PDU: {pdu_to_dict(pdu)}")

    def send_pdu_with_response(self, pdu, timeout=5):
        """
        Send a PDU and return a Deferred that will be called back on response.
        """
        request_id = getattr(pdu, "requestID", None)
        if request_id is None:
            raise ValueError("PDU must have a requestID for tracking responses.")

        deferred = defer.Deferred()
        self.pending_requests[request_id] = deferred

        # Set a timeout for the request
        reactor.callLater(timeout, self.handle_timeout, request_id)

        # Send the PDU
        self.send_pdu(pdu)
        return deferred
    
    def datagramReceived(self, data, addr):
        """
        Handle incoming PDUs.
        """
        try:
            pdu = PduFactory.create_pdu(data)
            print(f"Received PDU from {addr}: {pdu_to_dict(pdu)}")

            # Dispatch based on PDU type
            if isinstance(pdu, AcknowledgePdu):
                self.handle_acknowledge_pdu(pdu)
            elif isinstance(pdu, DataPdu):
                self.handle_data_pdu(pdu)
        except Exception as e:
            print(f"Error decoding PDU: {e}")

    def handle_acknowledge_pdu(self, pdu):
        """
        Process an AcknowledgePdu and trigger the corresponding Deferred.
        """
        request_id = pdu.requestID
        if request_id in self.pending_requests:
            deferred = self.pending_requests.pop(request_id)
            deferred.callback(pdu)  # Trigger the callback with the received PDU
            print(f"Acknowledgment received for request ID: {request_id}")

    def handle_timeout(self, request_id):
        """
        Handle a timeout for a pending request.
        """
        if request_id in self.pending_requests:
            deferred = self.pending_requests.pop(request_id)
            #deferred.errback(Exception(f"Request ID {request_id} timed out."))
            print(f"Request ID {request_id} timed out.")

    def handle_data_pdu(self, pdu):
        """
        Process a DataPdu and trigger the corresponding Deferred.
        """
        request_id = pdu.requestID
        if request_id in self.pending_requests:
            deferred = self.pending_requests.pop(request_id)
            deferred.callback(pdu)  # Trigger the callback with the received PDU
            print(f"DataPdu received for request ID: {request_id}")

    def emit_entity_state(self, entity_id, entity_type, position, velocity):
        print("Emitting entity state")
        pdu = EntityStatePdu()
        # Les 4 lignes suivantes ne devraient pas être nécessaires, mais sans elles, on a un bug en struct.pack au moment de la serialisation.
        pdu.pduStatus = 0
        pdu.entityAppearance=0
        pdu.capabilities=0
        pdu.pduType=1 

        pdu.exerciseID = 1
        pdu.protocolFamily = 1
        pdu.length = 144
        pdu.pduStatus = 6

        pdu.entityID.siteID = self.config["remote_dis_site"]
        pdu.entityID.applicationID = self.config["remote_dis_application"]
        pdu.entityID.entityID = entity_id

        pdu.forceId = 0 # 1: Friendly 2: Opposing [UID  6]

        pdu.deadReckoningParameters.deadReckoningAlgorithm = 4

        pdu.entityType.entityKind = entity_type["kind"]
        pdu.entityType.domain = entity_type["domain"]
        pdu.entityType.country = entity_type["country"]
        pdu.entityType.category = entity_type["category"]
        pdu.entityType.subcategory = entity_type["subcategory"]
        pdu.entityType.specific = entity_type["specific"]
        pdu.entityType.extra = entity_type["extra"]

        pdu.alternativeEntityType.entityKind = entity_type["kind"]
        pdu.alternativeEntityType.domain = entity_type["domain"]
        pdu.alternativeEntityType.country = entity_type["country"]
        pdu.alternativeEntityType.category = entity_type["category"]
        pdu.alternativeEntityType.subcategory = entity_type["subcategory"]
        pdu.alternativeEntityType.specific = entity_type["specific"]
        pdu.alternativeEntityType.extra = entity_type["extra"]

        

        pdu.entityLocation.x = position[0]
        pdu.entityLocation.y = position[1]
        pdu.entityLocation.z = position[2]

        # pdu.entityOrientation.psi   = 0
        # pdu.entityOrientation.theta = 0
        # pdu.entityOrientation.phi   = 0

        pdu.entityLinearVelocity.x = velocity[0]
        pdu.entityLinearVelocity.y = velocity[1]
        pdu.entityLinearVelocity.z = velocity[2]

        pdu.marking.characterSet=1
        pdu.marking.setString('MISSILE')

        self.send_pdu(pdu)


    def create_entity_sequence(self, entity_id, entity_type, position, velocity):
        """
        Cette méthode doit gérer le trafic DIS nécessaire pour créér un objet dans la simulation.

        IEEE 1278.1 Draft 16 rev 18: 
         - 85: Simulation management
         - 100: Entity creation
         - 360: format du CreateEntityPdu
         - 364: format du AcknowledgePdu
         - 370: format du SetDataPdu

        :param position: The position data in ECEF in m.
        :param valocity: The velocity in ECEF in m/s
        """
        print("Creating entity")
        # Step 1: Send CreateEntityPdu
        create_pdu = CreateEntityPdu()

        # Les lignes ci-dessous contournent l'exception struct.
        create_pdu.pduType=11
        create_pdu.pduStatus = 0

        create_pdu.originatingEntityID.siteID = self.config["own_dis_site"]
        create_pdu.originatingEntityID.applicationID = self.config["own_dis_application"]
        create_pdu.originatingEntityID.entityID = 0

        create_pdu.receivingEntityID.siteID = self.config["remote_dis_site"]
        create_pdu.receivingEntityID.applicationID = self.config["remote_dis_application"]
        create_pdu.receivingEntityID.entityID = entity_id

        create_pdu.requestID = self.get_requestID()

        create_pdu.entityType = entity_type

        d = self.send_pdu_with_response(create_pdu)

        # Step 2: On AcknowledgePdu, send SetDataPdu
        d.addCallback(lambda _: self.send_set_data_pdu(entity_id, entity_type, position, velocity))
        d.addErrback(lambda failure: print(f"CreateEntityPdu failed: {failure}"))

        # A retirer si on veut attendre un aknowledge avant d'envoyer le SetData.
        self.send_set_data_pdu(entity_id, entity_type, position, velocity)

    def send_set_data_pdu(self, entity_id, entity_type, position, velocity):
        """
        Send a SetDataPdu to set the position, route, and velocity of the entity.
        """

        set_data_pdu = SetDataPdu()
        # Les lignes ci-dessous contournent l'exception struct.
        set_data_pdu.pduType=19
        set_data_pdu.pduStatus = 0

        set_data_pdu.originatingEntityID.siteID = self.config["own_dis_site"]
        set_data_pdu.originatingEntityID.applicationID = self.config["own_dis_application"]
        set_data_pdu.originatingEntityID.entityID = 0

        set_data_pdu.receivingEntityID.siteID = self.config["remote_dis_site"]
        set_data_pdu.receivingEntityID.applicationID = self.config["remote_dis_application"]
        set_data_pdu.receivingEntityID.entityID = entity_id

        set_data_pdu.requestID = self.get_requestID()

        entityLocationX= EntityLocationDatum("X", position[0])
        entityLocationY= EntityLocationDatum("Y", position[1])
        entityLocationZ= EntityLocationDatum("Z", position[2])

        entityVelocityX= EntityLinearVelocityDatum("X", velocity[0])
        entityVelocityY= EntityLinearVelocityDatum("Y", velocity[1])
        entityVelocityZ= EntityLinearVelocityDatum("Z", velocity[2])

        # EntityOrientationDatum

        # entity_type = {"kind": 2, "domain": 6, "country": 71, "category": 1, "subcategory": 1}
        entityKind = EntityKindDatum(entity_type["kind"])
        entityDomain = EntityDomainDatum(entity_type["domain"])
        entityCountry = EntityCountryDatum(entity_type["country"])
        entityCategory = EntityCategoryDatum(entity_type["category"])
        entitySubCategory = EntitySubCategoryDatum(entity_type["subcategory"])

        set_data_pdu._datums = DatumSpecification([], [entityLocationX, 
                                                       entityLocationY, 
                                                       entityLocationZ,
                                                       entityVelocityX,
                                                       entityVelocityY,
                                                       entityVelocityZ,
                                                       entityKind,
                                                       entityDomain,
                                                       entityCountry,
                                                       entityCategory,
                                                       entitySubCategory])
        

        self.send_pdu(set_data_pdu)
        print(f"SetDataPdu sent for entity {entity_id}.")
