# -*- test-case-name: geotools.test.test_tools -*-
from opendis.RangeCoordinates import GPS
import math

gps = GPS() # conversion helper
    
def ECEF_to_natural_velocity(position, velocity):
    """
    Converts ECEF position and velocity to course and speed.

    Args:
        position: Object with .x, .y, .z (ECEF coordinates in meters).
        velocity: Object with .x, .y, .z (velocity in ECEF, m/s).

    Returns:
        (course, speed): Direction in degrees (0–360) and speed in m/s.
    """
    ecef_pos = (position.x, position.y, position.z)
    ecef_vel = (velocity.x, velocity.y, velocity.z)
    lat_deg, lon_deg, alt_deg = gps.ecef2lla(ecef_pos)
    # print(f"\npos={ecef_pos}, velocity={ecef_vel}")
    # print(f"lat_deg={lat_deg}, lon_deg={lon_deg}, alt_deg={alt_deg}")
    
    x_new = ecef_pos[0] + ecef_vel[0]
    y_new = ecef_pos[1] + ecef_vel[1]
    z_new = ecef_pos[2] + ecef_vel[2]

    new_lat_deg, new_lon_deg, new_alt_deg = gps.ecef2lla((x_new, y_new, z_new))
    # print(f"New position after 1 second: lat={new_lat_deg}, lon={new_lon_deg}, alt={new_alt_deg}")

    delta_lat = new_lat_deg - lat_deg
    delta_lon = new_lon_deg - lon_deg
    # print(f"delta_lat={delta_lat}")
    # print(f"delta_lon={delta_lon}")

    displacement_course = math.degrees(math.atan2(delta_lon, delta_lat)) % 360
    displacement_speed = math.sqrt(delta_lat**2 + delta_lon**2) * (1854.0 * 60.0)

    if displacement_speed < 1e-6:
        displacement_speed = 0.0

    # print(f"Displacement speed: {displacement_speed}")
    # print(f"Displacement course: {displacement_course}")

    return displacement_course, displacement_speed

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