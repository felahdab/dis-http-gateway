from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

from pydis.dis7 import (
    CreateEntityPdu,
    AcknowledgePdu,
    DataPdu,
    SetDataPdu,
)
import json
from socket import socket, AF_INET, SOCK_DGRAM
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

        # Set the socket options (e.g., broadcast or multicast)
        if self.config["mode"] == "broadcast":
            self.socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        elif self.config["mode"] == "multicast":
            self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.socket.bind((self.config["ip"], self.config["port"]))

    def send_pdu(self, pdu):
        """
        Encode and send a PDU over the network.
        """
        encoded_pdu = pdu.encode()
        destination = (self.config["ip"], self.config["port"])
        self.transport.write(encoded_pdu, destination)
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
            pdu = PduFactory().create_pdu(data)
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
            deferred.errback(Exception(f"Request ID {request_id} timed out."))

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
        # Step 1: Send CreateEntityPdu
        create_pdu = CreateEntityPdu()
        create_pdu.requestID = entity_id
        create_pdu.originatingEntityID.siteID = 1
        create_pdu.originatingEntityID.applicationID = 1
        create_pdu.originatingEntityID.entityID = entity_id
        create_pdu.entityType = entity_type

        d = self.send_pdu_with_response(create_pdu)

        # Step 2: On AcknowledgePdu, send SetDataPdu
        d.addCallback(lambda _: self.send_set_data_pdu(entity_id, position, velocity))
        d.addErrback(lambda failure: print(f"CreateEntityPdu failed: {failure}"))

    def send_set_data_pdu(self, entity_id, position, velocity):
        """
        Send a SetDataPdu to set the position, route, and velocity of the entity.
        """

        set_data_pdu = SetDataPdu()
        set_data_pdu.requestID = entity_id
        set_data_pdu.originatingEntityID.siteID = 1
        set_data_pdu.originatingEntityID.applicationID = 1
        set_data_pdu.originatingEntityID.entityID = entity_id

        # A modifier: la génération d'un SetDataPdu ne se passe pas comme ça.
        # Il faut remplacer le code ci-dessous par un truc du genre:
        # set_data_pdu.self._datums = DatumSpecification([], variableDatumRecords)
        # et initialiser variableDatumRecord avec les informations de position et la velocité.
        # Voir SISO-REF010 page 725 pour les ID des Datums correspondants.

        # Set the data fields for position, route, and velocity
        set_data_pdu.variableDatumID = 1  # Example ID for position and velocity
        set_data_pdu.variableDatumValue = json.dumps(
            {"position": position, "velocity": velocity}
        ).encode()

        self.send_pdu(set_data_pdu)
        print(f"SetDataPdu sent for entity {entity_id}.")
