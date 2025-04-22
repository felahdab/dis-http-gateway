# -*- test-case-name: simtools.test.test_objects -*-
import datetime
import math

from geopy import distance

from opendis.RangeCoordinates import GPS
from distools.geotools.tools import natural_velocity_to_ECEF

gps = GPS()

class Missile():
    def __init__(self, entity_id, entity_type, emitter, initial_position, course, speed, range):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.emitter = emitter
        self.initial_timestamp = datetime.datetime.now().timestamp()
        self.initial_position = initial_position # [latitude, longitude, altitude]
        self.course = course
        self.speed = speed
        self.current_position = self.initial_position # [latitude, longitude, altitude]
        self.current_timestamp = self.initial_timestamp
        self.range = range
        self.loop = None
        self.is_out_of_range = False

    def setLoop(self, loop):
        self.loop = loop

    def stopLoop(self):
        self.loop.stop()

    def update(self):
        nowtimestamp = datetime.datetime.now().timestamp()
        deltatime = nowtimestamp - self.current_timestamp
        newposition = self.advance(deltatime)

        self.current_position = newposition
        self.current_timestamp = nowtimestamp

        self.emit()

        dist = distance.distance(self.current_position, self.initial_position).km

        print("Distance from shooting point: ", dist)
        if  dist > self.range:
            self.is_out_of_range = True
            self.stopLoop()

        return

    def advance(self, deltatime):
        latitude_variation = deltatime * math.cos(math.radians(self.course)) * self.speed / ( 1854.0 * 60.0 )
        longitude_variation = deltatime * math.sin(math.radians(self.course)) * self.speed / ( 1854.0 * 60.0 * math.cos(math.radians(self.current_position[0])) ) 
        newposition = [ self.current_position[0] + latitude_variation, self.current_position[1] + longitude_variation, self.current_position[2]]
        return newposition

    def emit(self):
        [lat, lon, alt] = self.current_position
        (X, Y, Z) = gps.lla2ecef( [lat, lon, alt])
        (Xvel, Yvel, Zvel) = natural_velocity_to_ECEF(lat, lon, alt, self.course, self.speed)


        position = (X, Y, Z)  # Coordonnées de l'entité
        velocity = (Xvel, Yvel, Zvel)  # Vitesse de l'entité

        self.emitter.emit_entity_state(self.entity_id, self.entity_type, position, velocity)
        
    def get_missile_is_out_of_range(self):
        return self.is_out_of_range