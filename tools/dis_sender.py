#!python

__author__ = "DMcG"
__date__ = "$Jun 23, 2015 10:27:29 AM$"

import socket
import time

from io import BytesIO

from opendis.DataOutputStream import DataOutputStream
from opendis.dis7 import EntityStatePdu
from opendis.RangeCoordinates import GPS, deg2rad

import pprint

UDP_PORT = 3000
DESTINATION_ADDRESS = "192.168.84.1"

udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

gps = GPS() # conversion helper

def send():
    
    pdu = EntityStatePdu()
    pdu.entityID.entityID = 42
    pdu.entityID.siteID = 17
    pdu.entityID.applicationID = 23
    pdu.marking.setString('C2N')
    # Les 4 lignes suivantes ne devraient pas être nécessaires, mais sans elles, on a un bug en struct.pack au moment de la serialisation.
    pdu.pduStatus = 0
    pdu.entityAppearance=0
    pdu.capabilities=0
    pdu.pduType=1 

    toulonLocation = gps.llarpy2ecef(deg2rad(43.0),   # longitude (radians)
                                       deg2rad(6.0), # latitude (radians)
                                       1,               # altitude (meters)
                                       0,               # roll (radians)
                                       0,               # pitch (radians)
                                       0                # yaw (radians)
                                       )

    pdu.entityLocation.x = toulonLocation[0]
    pdu.entityLocation.y = toulonLocation[1]
    pdu.entityLocation.z = toulonLocation[2]
    pdu.entityOrientation.psi   = toulonLocation[3]
    pdu.entityOrientation.theta = toulonLocation[4]
    pdu.entityOrientation.phi   = toulonLocation[5]

    memoryStream = BytesIO()
    outputStream = DataOutputStream(memoryStream)
    pdu.serialize(outputStream)
    data = memoryStream.getvalue()

    while True:
        udpSocket.sendto(data, (DESTINATION_ADDRESS, UDP_PORT))
        print("Sent {}. {} bytes".format(pdu.__class__.__name__, len(data)))
        time.sleep(5)

send()
