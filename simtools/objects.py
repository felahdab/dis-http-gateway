# -*- test-case-name: simtools.test.test_objects -*-
import datetime
import math

from geopy import distance

from opendis.RangeCoordinates import GPS
from distools.geotools.tools import natural_velocity_to_ECEF

gps = GPS()

class Missile():
    def __init__(self, entity_id, entity_type, emitter, initial_position, course, speed, range, initial_timestamp, endpoint_time, max_flight_time, STN, target_latitude, target_longitude):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.emitter = emitter
        self.is_out_of_range = True if ((endpoint_time - initial_timestamp) > max_flight_time) else False
        self.initial_timestamp = initial_timestamp
        self.initial_position = initial_position # [latitude, longitude, altitude]
        self.course = course
        self.speed = speed
        self.current_position = initial_position # Set current position as its needed by advance()
        self.current_position = self.advance(endpoint_time - initial_timestamp)
        self.current_timestamp = datetime.datetime.now().timestamp()
        self.range = range
        self.STN = STN
        self.target_latitude = target_latitude
        self.target_longitude = target_longitude
        self.loop = None 

    def setLoop(self, loop):
        """
        Sets a loop for a missile position update 

        Args:
            loop: task.LoopingCall() loop
        """
        self.loop = loop

    def stopLoop(self):
        """
        Stops missile update loop when it has reached its maximum range
        """
        self.loop.stop()

    def update(self):
        """
        Updates a missile position depending on the time elapsed and sends it over the network.
        If the missile has reached its maximum range, stops its loop.
        """
        nowtimestamp = datetime.datetime.now().timestamp()
        deltatime = nowtimestamp - self.current_timestamp
        newposition = self.advance(deltatime)

        self.current_position = newposition
        self.current_timestamp = nowtimestamp

        self.emit()

        dist = distance.distance(self.current_position, self.initial_position).km

        print("[DIS INFO] Distance from shooting point: ", dist)
        if  dist > self.range:
            self.is_out_of_range = True
            self.stopLoop()

        return

    def advance(self, deltatime):
        """
        Computes the new position of a missile based on its speed, course, and elapsed time.
        Altitude remains unchanged.

        Args:
            deltatime: The time elapsed in seconds.

        Returns:
            The new position as a list in the format [latitude, longitude, altitude].
        """
        latitude_variation = deltatime * math.cos(math.radians(self.course)) * self.speed / ( 1854.0 * 60.0 )
        longitude_variation = deltatime * math.sin(math.radians(self.course)) * self.speed / ( 1854.0 * 60.0 * math.cos(math.radians(self.current_position[0])) ) 
        newposition = [ self.current_position[0] + latitude_variation, self.current_position[1] + longitude_variation, self.current_position[2]]
        return newposition

    def emit(self):
        """
        Emits the current state of the missile over the network, including position and velocity, in ECEF coordinates.
        """
        [lat, lon, alt] = self.current_position
        (X, Y, Z) = gps.lla2ecef( [lat, lon, alt])
        (Xvel, Yvel, Zvel) = natural_velocity_to_ECEF(lat, lon, alt, self.course, self.speed)


        position = (X, Y, Z)  # Coordonnées de l'entité
        velocity = (Xvel, Yvel, Zvel)  # Vitesse de l'entité

        self.emitter.emit_entity_state(self.entity_id, self.entity_type, position, velocity)

        self.emitter.emit_custom_pdu(self.STN, self.target_latitude, self.target_longitude)