from opendis.RangeCoordinates import GPS, deg2rad

import math

gps = GPS() # conversion helper

def natural_velocity_to_ECEF(latitude, longitude, altitude, course, speed):
    # latitude: in degrees
    # longitude: in degrees
    # altitude: in meters
    # course: in degrees
    # speed: in meters per second

    initial_position = gps.llarpy2ecef(deg2rad(longitude),   # longitude (radians)
                                       deg2rad(latitude), # latitude (radians)
                                       altitude,               # altitude (meters)
                                       0,               # roll (radians)
                                       0,               # pitch (radians)
                                       0                # yaw (radians)
                                       )
    
    latitude_variation_one_second = math.cos(deg2rad(course)) * speed
    longitude_variation_one_second = math.sin(deg2rad(course)) * speed

    latitude_after_one_second = latitude + latitude_variation_one_second
    longitude_after_one_second = longitude + longitude_variation_one_second

    position_after_one_second = gps.llarpy2ecef(deg2rad(longitude_after_one_second),   # longitude (radians)
                                       deg2rad(latitude_after_one_second), # latitude (radians)
                                       altitude,               # altitude (meters)
                                       0,               # roll (radians)
                                       0,               # pitch (radians)
                                       0                # yaw (radians)
                                       )
    
    Xvelocity = position_after_one_second[0] - initial_position[0]
    Yvelocity = position_after_one_second[1] - initial_position[1]
    Zvelocity = position_after_one_second[2] - initial_position[2]

    # Returns velocity in ECEF frame
    # Each coordinate in meters per second
    return [Xvelocity, Yvelocity, Zvelocity]