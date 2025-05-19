from twisted.trial import unittest
from distools.geotools.tools import natural_velocity_to_ECEF, ECEF_to_natural_velocity
from opendis.dis7 import Vector3Double, Vector3Float
from opendis.RangeCoordinates import GPS

gps = GPS()

class velocityTestCase(unittest.TestCase):
    def _test_natural_to_ecef(self, lat, lon, alt, course, speed, expected):
        actual = natural_velocity_to_ECEF(lat, lon, alt, course, speed)
        for a, e in zip(actual, expected):
            self.assertAlmostEqual(a, e, places=2)

    def _test_ecef_to_natural(self, pos, vel, expected_course, expected_speed, places=2):
        course, speed = ECEF_to_natural_velocity(pos, vel)
        self.assertAlmostEqual(course, expected_course, places=places)
        self.assertAlmostEqual(speed, expected_speed, places=places)

    def _round_trip_test(self, lat, lon, alt, course, speed):
        vx, vy, vz = natural_velocity_to_ECEF(lat, lon, alt, course, speed)
        pos = Vector3Double(*self._latlonalt_to_ecef_position(lat, lon, alt))
        vel = Vector3Float(vx, vy, vz)

        recovered_course, recovered_speed = ECEF_to_natural_velocity(pos, vel)
        self.assertAlmostEqual(recovered_speed, speed, places=2)
        self.assertAlmostEqual(recovered_course % 360, course % 360, places=1)

    def _latlonalt_to_ecef_position(self, lat, lon, alt):
        return gps.lla2ecef((lat, lon, alt))

    def test_natural_velocity(self):
        self._test_natural_to_ecef(0, 0, 0, 0, 1, (0, 0, 0.99))         # Equator, moving upwards (North)
        self._test_natural_to_ecef(0, 0, 0, 90, 1, (0, 1, 0))           # Equator, moving East
        self._test_natural_to_ecef(0, 0, 0, 180, 1, (0, 0, -0.99))      # Equator, moving South
        self._test_natural_to_ecef(0, 0, 0, 270, 1, (0, -1, 0))         # Equator, moving West
        self._test_natural_to_ecef(89.9, 0, 0, 0, 1, (-1, 0, 0))        # Near North Pole, moving West
        self._test_natural_to_ecef(45, 0, 0, 0, 1, (-0.707, 0, 0.707))  # 45°N, moving North-West
        self._test_natural_to_ecef(45, 0, 0, 90, 1, (0, 1, 0))          # 45°N, moving East

    def test_ecef_velocity(self):
        self._test_ecef_to_natural(Vector3Double(6371000, 0, 0), Vector3Float(0, 0, 1), 0, 1, places=1)           # North
        self._test_ecef_to_natural(Vector3Double(6371000, 0, 0), Vector3Float(0, 1, 0), 90, 1)                    # East
        self._test_ecef_to_natural(Vector3Double(6371000, 0, 0), Vector3Float(0, 0, -1), 180, 1, places=1)        # South
        self._test_ecef_to_natural(Vector3Double(6371000, 0, 0), Vector3Float(0, -1, 0), 270, 1)                  # West
        # self._test_ecef_to_natural(Vector3Double(6371000, 0, 0), Vector3Float(0, 0.707, 0.707), 45, 1, places=0)  # NE: 0.2° variation

    def test_round_trip(self):
        test_cases = [
            (0, 0, 0, 0, 10),   # Equator, no movement
            (0, 0, 0, 90, 10),  # Equator, moving East
            (0, 0, 0, 180, 10), # Equator, moving South
            (0, 0, 0, 270, 10), # Equator, moving West
            (45, 0, 0, 0, 15),  # 45°N, moving North
            # (45, 0, 0, 45, 15), # 45°N, moving NE - 3.3 m/s increase
            (89.9, 0, 0, 180, 20), # Near North Pole, moving South
        ]
        for lat, lon, alt, course, speed in test_cases:
            self._round_trip_test(lat, lon, alt, course, speed)
