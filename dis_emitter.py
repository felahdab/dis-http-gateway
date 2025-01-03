from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from pydis.dis7 import EntityStatePdu
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
        self.socket = socket(AF_INET, SOCK_DGRAM)  # Create a UDP socket

        # Set the socket options (e.g., broadcast or multicast)
        if self.config["mode"] == "broadcast":
            self.socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        elif self.config["mode"] == "multicast":
            self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.socket.bind((self.config["ip"], self.config["port"]))

    def send_pdu(self, position, route, speed):
        """
        Cette méthode doit gérer le trafic DIS nécessaire pour créér un objet dans la simulation.

        IEEE 1278.1 Draft 16 rev 18: 
         - 85: Simulation management
         - 100: Entity creation
         - 360: format du CreateEntityPdu
         - 364: format du AcknowledgePdu
         - 368: format du DataQueryPdu
         - 370: format du SetDataPdu

        :param position: The position data (latitude, longitude, etc.)
        :param route: The route data (if any)
        :param speed: The speed data
        """
        # Create and send a PDU
        
        pdu = EntityStatePdu()
        pdu.entityLocation.x = position[0]
        pdu.entityLocation.y = position[1]
        pdu.entityLocation.z = position[2]
        pdu.entityLinearVelocity.x = speed
        pdu.entityOrientation.psi = route  # Assuming psi for route

        # Send the PDU to the configured destination
        if self.config["mode"] == "unicast":
            # Unicast: send to a specific IP address
            self.socket.sendto(pdu.encode(), (self.config["ip"], self.config["port"]))
        elif self.config["mode"] == "broadcast":
            # Broadcast: send to all devices in the network
            self.socket.sendto(pdu.encode(), ("<broadcast>", self.config["port"]))
        elif self.config["mode"] == "multicast":
            # Multicast: send to a multicast group
            self.socket.sendto(pdu.encode(), (self.config["ip"], self.config["port"]))

        print(f"Sent PDU to {self.config['mode']} destination: {self.config['ip']}:{self.config['port']}")
