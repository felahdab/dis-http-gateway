# -*- test-case-name: geotools.test.test_tools -*-
from opendis.RangeCoordinates import GPS, deg2rad

import math

gps = GPS() # conversion helper

def natural_velocity_to_ECEF(latitude, longitude, altitude, course, speed):
    # latitude: in degrees
    # longitude: in degrees
    # altitude: in meters
    # course: in degrees
    # speed: in meters per second

    #print("Latitude et longitude initiale: ", latitude, longitude)

    initial_position = gps.lla2ecef([latitude, longitude, altitude])
    
    #print("Position ECEF initiale: ", initial_position)
    
    latitude_variation_one_second = math.cos(math.radians(course)) * speed / ( 1854.0 * 60.0 )
    longitude_variation_one_second = math.sin(math.radians(course)) * speed / ( 1854.0 * 60.0 * math.cos(math.radians(latitude)) ) 

    #print("Variation de latitude et de longitude: ", latitude_variation_one_second, longitude_variation_one_second)


    latitude_after_one_second = latitude + latitude_variation_one_second
    longitude_after_one_second = longitude + longitude_variation_one_second

    #print("Latitude et de longitude apres 1 seconde: ", latitude_after_one_second, longitude_after_one_second)

    position_after_one_second = gps.lla2ecef([latitude_after_one_second, longitude_after_one_second, altitude])
    
    #print(position_after_one_second)
    
    Xvelocity = position_after_one_second[0] - initial_position[0]
    Yvelocity = position_after_one_second[1] - initial_position[1]
    Zvelocity = position_after_one_second[2] - initial_position[2]

    # Returns velocity in ECEF frame
    # Each coordinate in meters per second
    #print()
    return (Xvelocity, Yvelocity, Zvelocity)