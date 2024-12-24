import time
import sys
import array
import os

from opendis.dis7 import *
from opendis.RangeCoordinates import *
from opendis.PduFactory import createPdu

from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol
from twisted.web.client import Agent, BrowserLikePolicyForHTTPS
from twisted.web.http_headers import Headers

from twisted.internet.defer import succeed

DIS_LISTEN_PORT=int(os.getenv("DIS_LISTEN_PORT", 3000))

HTTP_API_ENDPOINT=os.getenv("HTTP_API_ENDPOINT", "http://web/api/v1/messagedis")
HTTP_AUTH_TOKEN=os.getenv("HTTP_AUTH_TOKEN", "changeme")

gps = GPS()

class DISReceiver(DatagramProtocol):
    def __init__(self, http_api_client):
        self.http_api_client = http_api_client

    def datagramReceived(self, datagram, address):
        #print(f"received {datagram!r} from {address}")
        pdu = createPdu(datagram);
        pduTypeName = pdu.__class__.__name__

        if pdu.pduType == 1: # PduTypeDecoders.EntityStatePdu:
            loc = (pdu.entityLocation.x, 
                pdu.entityLocation.y, 
                pdu.entityLocation.z,
                pdu.entityOrientation.psi,
                pdu.entityOrientation.theta,
                pdu.entityOrientation.phi
                )

            body = gps.ecef2llarpy(*loc)

            print("Received {}\n".format(pduTypeName)
                + " Id        : {}\n".format(pdu.entityID.entityID)
                + " Latitude  : {:.2f} degrees\n".format(rad2deg(body[0]))
                + " Longitude : {:.2f} degrees\n".format(rad2deg(body[1]))
                + " Altitude  : {:.0f} meters\n".format(body[2])
                + " Yaw       : {:.2f} degrees\n".format(rad2deg(body[3]))
                + " Pitch     : {:.2f} degrees\n".format(rad2deg(body[4]))
                + " Roll      : {:.2f} degrees\n".format(rad2deg(body[5]))
                )
            #self.http_api_client.post_content("Message_received")

        else:
            print("Received {}, {} bytes".format(pduTypeName, len(datagram)), flush=True)


class BytesProducer(object):
    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass

class HttpApiClient(Agent):
    def __init__(self, 
                reactor, 
                contextFactory=BrowserLikePolicyForHTTPS(), 
                connectTimeout=None, 
                bindAddress=None, 
                pool=None,
                uri="",
                headers=[]):
        Agent.__init__(self, reactor, contextFactory, connectTimeout, bindAddress, pool)
        self.uri = uri

    def post_content(self, content):
        self.request("POST", self.uri, headers=self.headers, bodyProducer=BytesProducer(content))

if __name__ == "__main__":
    print("Starting DIS/HTTP gateway.")
    print("UDP Listening port: {}\n".format(DIS_LISTEN_PORT))
    print("HTTP endpoint: {}".format(HTTP_API_ENDPOINT))
    print("HTTP auth token: {}\n".format(HTTP_AUTH_TOKEN))

    http_api_client = HttpApiClient(reactor, headers=[{'Authorization': ['Bearer: ' + HTTP_AUTH_TOKEN]}])

    reactor.listenUDP(DIS_LISTEN_PORT, DISReceiver(http_api_client))
    
    reactor.run()