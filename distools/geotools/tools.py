# -*- test-case-name: geotools.test.test_tools -*-
from opendis.RangeCoordinates import GPS, deg2rad

import math

gps = GPS() # conversion helper

def natural_velocity_to_ECEF(latitude, longitude, altitude, course, speed):
    """
    Converts natural velocity (course and speed) into ECEF (Earth-Centered, Earth-Fixed) velocity components.

    Given a geodetic position (latitude, longitude, altitude) and a movement vector (course in degrees, 
    speed in meters per second), this function estimates the velocity in the ECEF frame by computing the 
    position after one second and deriving the displacement vector.

    Args:
        latitude (float): Latitude in degrees.
        longitude (float): Longitude in degrees.
        altitude (float): Altitude in meters.
        course (float): Movement direction in degrees (0° is North, 90° is East).
        speed (float): Speed in meters per second.

    Returns:
        A tuple of three floats representing velocity in the ECEF frame (X, Y, Z), in meters per second.
    """

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