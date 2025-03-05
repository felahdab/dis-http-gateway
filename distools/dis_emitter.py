from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor, defer

from opendis.dis7 import (
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
        self.requestID = 1029

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
        print(f"Sent PDU: {pdu}")

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
            print(f"Received PDU from {addr}: {pdu}")

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

    def create_entity_sequence(self, entity_id, entity_type, position, velocity):
        """
        Cette méthode doit gérer le trafic DIS nécessaire pour créér un objet dans la simulation.

        IEEE 1278.1 Draft 16 rev 18: 
         - 85: Simulation management
         - 100: Entity creation
         - 360: format du CreateEntityPdu
         - 364: format du AcknowledgePdu
         - 370: format du SetDataPdu

        :param position: The position data (latitude, longitude, etc.)
        :param route: The route data (if any)
        :param speed: The speed data
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

        entityDISLocation = GPS().llarpy2ecef(deg2rad(36.6),   # longitude (radians)
                                       deg2rad(-121.9), # latitude (radians)
                                       0,               # altitude (meters)
                                       0,               # roll (radians)
                                       0,               # pitch (radians)
                                       0                # yaw (radians)
                                       )
        entityLocationX= EntityLocationDatum("X", entityDISLocation[0])
        entityLocationY= EntityLocationDatum("Y", entityDISLocation[1])
        entityLocationZ= EntityLocationDatum("Z", entityDISLocation[2])

        entityVelocityX= EntityLinearVelocityDatum("X", 0)
        entityVelocityY= EntityLinearVelocityDatum("Y", 0)
        entityVelocityZ= EntityLinearVelocityDatum("Z", 0)

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
