from io import BytesIO

from twisted.internet.defer import ensureDeferred
from twisted.internet.protocol import DatagramProtocol

from opendis.DataOutputStream import DataOutputStream
from opendis.RangeCoordinates import GPS
from opendis.dis7 import EntityStatePdu, EntityType, Vector3Double, Vector3Float
from opendis import PduFactory
from .pdus.tools import pdu_to_dict
from enum import IntEnum

gps = GPS()

ENTITY_TYPE_MAP = {
    (1, 2, 78, 22, 2, 0): "NH90",
    (2, 6, 71, 1, 1, 4): "ExocetMM40",
    (1, 3, 62, 6, 5, 1): "Normandie",
}

class IPTransmissionType(IntEnum):
    UNICAST = 0
    MULTICAST = 1
    BROADCAST = 2

class DISCommunicator(DatagramProtocol):
    def __init__(self, http_poster, receiver, emitter, remote_dis_site):
        self.pdu_factory = PduFactory
        self.http_poster = http_poster
        self.recv_addr = receiver["ip"]
        self.recv_mode = IPTransmissionType(receiver["mode"])
        self.send_mode = IPTransmissionType(emitter["mode"])
        self.send_addr = "<broadcast>" if self.send_mode == IPTransmissionType.BROADCAST else emitter["ip"]
        self.send_port = emitter["port"]
        self.remote_dis_site = remote_dis_site
        self.loop = None

    def startProtocol(self):
        print(f"[DIS INFO] DISEmitter started in {self.send_mode.name} mode.")
        # RECEIVER setup
        if (self.recv_mode == IPTransmissionType.MULTICAST):
            self.transport.joinGroup(self.recv_addr)
            print(f"[DIS INFO] Joined multicast group {self.recv_addr}")
        elif (self.recv_mode == IPTransmissionType.BROADCAST):
            self.transport.setBroadcastAllowed(True)

        # EMITTER setup
        print(f"[DIS INFO] DISReceiver started in {self.send_mode.name} mode.")
        if (self.send_mode == IPTransmissionType.MULTICAST):
            self.transport.joinGroup(self.send_group_ip)
            print(f"[DIS INFO] Joined multicast group {self.send_addr}")
        elif (self.send_mode == IPTransmissionType.BROADCAST):
            self.transport.setBroadcastAllowed(True)

    def datagramReceived(self, data, addr):
        ensureDeferred(self.handle_pdu(data, addr))
            
    async def handle_pdu(self, data, addr):
        """
        Upon reception of a datagram, creates a PDU from it and POST it to the API if its an EntityStatePDU

        Args:
            data: Datagram received from the socket
            addr: Source address of the datagram
        """
        try:
            pdu = self.pdu_factory.createPdu(data)
            if pdu:
                pdu_json = pdu_to_dict(pdu)            
                # pprint(pdu_json)
                if self.should_relay_pdu(pdu):
                    EID = pdu.entityID
                    print(f"[DIS RECV] {self.get_entity_name(pdu):<10} Entity with SN={EID.siteID:<2}, AN={EID.applicationID:<3}, EN={EID.entityID:<3} from {addr[0]}")
                    ecef = (pdu.entityLocation.x, pdu.entityLocation.y, pdu.entityLocation.z)
                    real_world_location = gps.ecef2lla(ecef)
                    pdu_json["real_world_location"] = real_world_location
                    await self.http_poster.post_to_api(pdu_json, is_ack=False)
        except Exception as e:
            print(f"Error decoding PDU: {e}")
 
    def get_entity_name(self, pdu="Unkown"):
        entity_type = pdu.entityType
        return ENTITY_TYPE_MAP.get((entity_type.entityKind, entity_type.domain, entity_type.country, entity_type.category, entity_type.subcategory, entity_type.specific), "UnknownEntity")

    def send_pdu(self, pdu):
        """
        Converts the given PDU from JSON to network stream and sends it over the network
        
        Args:
            pdu: PDU to send
        """
        memoryStream = BytesIO()
        outputStream = DataOutputStream(memoryStream)
        pdu.serialize(outputStream)
        data = memoryStream.getvalue()
        self.transport.write(data, (self.send_addr, self.send_port))
        EID = pdu.entityID
        print(f"[DIS SEND] {self.get_entity_name(pdu)} Entity with SN={EID.siteID:<2}, AN={EID.applicationID:<3}, EN={EID.entityID:<3} sent to {self.send_addr}:{self.send_port}")

    def should_relay_pdu(self, pdu):
        """
        Verifies whether the given pdu is an EntityStatePDU or not.
        
        Args:
            pdu: PDU to verify

        Returns:
            True if the given pdu is an EntityStatePDU, otherwise False
        """
        return isinstance(pdu, EntityStatePdu)
    
    def emit_entity_state(self, entity_id, entity_type, position, velocity):
        """
        Creates and sends an EntityState PDU.
        
        Args:
            entity_id: Entity ID of the PDU to send
            entity_type: Entity Type of the PDU to send
            position: Position of the PDU to send
            velocity: Velocity of the PDU to send
        """
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
        pdu.entityID = entity_id
        pdu.deadReckoningParameters.deadReckoningAlgorithm = 4 # DRM (RVW) - High Speed or Maneuvering Entity with Extrapolation of Orientation [UID 44]

        pdu.forceId = 0 # 1: Friendly 2: Opposing [UID  6]

        pdu.entityType = EntityType(entity_type["kind"], entity_type["domain"], entity_type["country"], entity_type["category"], entity_type["subcategory"], entity_type["specific"], entity_type["extra"])
        pdu.entityLocation = Vector3Double(position[0], position[1], position[2])
        pdu.entityLinearVelocity = Vector3Float(velocity[0], velocity[1], velocity[2])
        pdu.marking.characterSet = 1  # ASCII [UID 45]
        pdu.marking.setString("MISSILE")

        self.send_pdu(pdu)
    
    def get_RemoteDISSite(self):
        """
        Gets the remote DIS site (Site ID) initially configured in the env file
        
        Returns:
            remote_dis_site
        """
        return self.remote_dis_site


    # def get_requestID(self):
    #     ret = self.requestID
    #     self.requestID = self.requestID + 1
    #     return ret
    
    # def handle_acknowledge_pdu(self, pdu):
    #     """
    #     Process an AcknowledgePdu and trigger the corresponding Deferred.
    #     """
    #     request_id = pdu.requestID
    #     if request_id in self.pending_requests:
    #         deferred = self.pending_requests.pop(request_id)
    #         deferred.callback(pdu)  # Trigger the callback with the received PDU
    #         print(f"Acknowledgment received for request ID: {request_id}")

    # def handle_timeout(self, request_id):
    #     """
    #     Handle a timeout for a pending request.
    #     """
    #     if request_id in self.pending_requests:
    #         deferred = self.pending_requests.pop(request_id)
    #         #deferred.errback(Exception(f"Request ID {request_id} timed out."))
    #         print(f"Request ID {request_id} timed out.")

    # def handle_data_pdu(self, pdu):
    #     """
    #     Process a DataPdu and trigger the corresponding Deferred.
    #     """
    #     request_id = pdu.requestID
    #     if request_id in self.pending_requests:
    #         deferred = self.pending_requests.pop(request_id)
    #         deferred.callback(pdu)  # Trigger the callback with the received PDU
    #         print(f"DataPdu received for request ID: {request_id}")

    # def send_pdu_with_response(self, pdu, timeout=5):
    #     """
    #     Send a PDU and return a Deferred that will be called back on response.
    #     """
    #     request_id = getattr(pdu, "requestID", None)
    #     if request_id is None:
    #         raise ValueError("PDU must have a requestID for tracking responses.")

    #     deferred = defer.Deferred()
    #     self.pending_requests[request_id] = deferred

    #     # Set a timeout for the request
    #     reactor.callLater(timeout, self.handle_timeout, request_id)

    #     # Send the PDU
    #     self.send_pdu(pdu)
    #     return deferred
    
    # def create_entity_sequence(self, entity_id, entity_type, position, velocity):
    #     """
    #     Cette méthode doit gérer le trafic DIS nécessaire pour créér un objet dans la simulation.

    #     IEEE 1278.1 Draft 16 rev 18: 
    #      - 85: Simulation management
    #      - 100: Entity creation
    #      - 360: format du CreateEntityPdu
    #      - 364: format du AcknowledgePdu
    #      - 370: format du SetDataPdu

    #     :param position: The position data in ECEF in m.
    #     :param valocity: The velocity in ECEF in m/s
    #     """
    #     print("Creating entity")
    #     # Step 1: Send CreateEntityPdu
    #     create_pdu = CreateEntityPdu()

    #     # Les lignes ci-dessous contournent l'exception struct.
    #     create_pdu.pduType=11
    #     create_pdu.pduStatus = 0

    #     create_pdu.originatingEntityID.siteID = self.config["own_dis_site"]
    #     create_pdu.originatingEntityID.applicationID = self.config["own_dis_application"]
    #     create_pdu.originatingEntityID.entityID = 0

    #     create_pdu.receivingEntityID.siteID = self.config["remote_dis_site"]
    #     create_pdu.receivingEntityID.applicationID = self.config["remote_dis_application"]
    #     create_pdu.receivingEntityID.entityID = entity_id

    #     create_pdu.requestID = self.get_requestID()

    #     create_pdu.entityType = entity_type

    #     d = self.send_pdu_with_response(create_pdu)

    #     # Step 2: On AcknowledgePdu, send SetDataPdu
    #     d.addCallback(lambda _: self.send_set_data_pdu(entity_id, entity_type, position, velocity))
    #     d.addErrback(lambda failure: print(f"CreateEntityPdu failed: {failure}"))

    #     # A retirer si on veut attendre un aknowledge avant d'envoyer le SetData.
    #     self.send_set_data_pdu(entity_id, entity_type, position, velocity)

    # def send_set_data_pdu(self, entity_id, entity_type, position, velocity):
    #     """
    #     Send a SetDataPdu to set the position, route, and velocity of the entity.
    #     """

    #     set_data_pdu = SetDataPdu()
    #     # Les lignes ci-dessous contournent l'exception struct.
    #     set_data_pdu.pduType=19
    #     set_data_pdu.pduStatus = 0

    #     set_data_pdu.originatingEntityID.siteID = self.config["own_dis_site"]
    #     set_data_pdu.originatingEntityID.applicationID = self.config["own_dis_application"]
    #     set_data_pdu.originatingEntityID.entityID = 0

    #     set_data_pdu.receivingEntityID.siteID = self.config["remote_dis_site"]
    #     set_data_pdu.receivingEntityID.applicationID = self.config["remote_dis_application"]
    #     set_data_pdu.receivingEntityID.entityID = entity_id

    #     set_data_pdu.requestID = self.get_requestID()

    #     entityLocationX= EntityLocationDatum("X", position[0])
    #     entityLocationY= EntityLocationDatum("Y", position[1])
    #     entityLocationZ= EntityLocationDatum("Z", position[2])

    #     entityVelocityX= EntityLinearVelocityDatum("X", velocity[0])
    #     entityVelocityY= EntityLinearVelocityDatum("Y", velocity[1])
    #     entityVelocityZ= EntityLinearVelocityDatum("Z", velocity[2])

    #     # EntityOrientationDatum

    #     # entity_type = {"kind": 2, "domain": 6, "country": 71, "category": 1, "subcategory": 1}
    #     entityKind = EntityKindDatum(entity_type["kind"])
    #     entityDomain = EntityDomainDatum(entity_type["domain"])
    #     entityCountry = EntityCountryDatum(entity_type["country"])
    #     entityCategory = EntityCategoryDatum(entity_type["category"])
    #     entitySubCategory = EntitySubCategoryDatum(entity_type["subcategory"])

    #     set_data_pdu._datums = DatumSpecification([], [entityLocationX, 
    #                                                    entityLocationY, 
    #                                                    entityLocationZ,
    #                                                    entityVelocityX,
    #                                                    entityVelocityY,
    #                                                    entityVelocityZ,
    #                                                    entityKind,
    #                                                    entityDomain,
    #                                                    entityCountry,
    #                                                    entityCategory,
    #                                                    entitySubCategory])
        

        # self.send_pdu(set_data_pdu)
        # print(f"SetDataPdu sent for entity {entity_id}.")