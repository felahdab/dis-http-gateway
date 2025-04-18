from twisted.trial import unittest
from distools.geotools.tools import natural_velocity_to_ECEF

class velocityTestCase(unittest.TestCase):
    def _test(self, lat, lon, alt, course, speed, expected):
        actual = natural_velocity_to_ECEF(lat, lon, alt, course, speed)
        for a, e in zip(actual, expected):
            self.assertAlmostEqual(a, e, places=2)
        
    def test_velocity_north(self):
        self._test(0, 0, 0, 0, 1, (0, 0, 0.99))

    def test_velocity_east(self):
        self._test(0, 0, 0, 90, 1, (0, 1, 0))

    def test_velocity_south(self):
        self._test(0, 0, 0, 180, 1, (0, 0, -0.99))

    def test_velocity_west(self):
        self._test(0, 0, 0, 270, 1, (0, -1, 0))

    def test_velocity_near_north_pole(self):
        self._test(89.9, 0, 0, 0, 1, (-1, 0, 0))

    def test_velocity_diagonal_45deg(self):
        self._test(45, 0, 0, 0, 1, (-0.707, 0, 0.707))

    def test_velocity_east_at_45deg(self):
        self._test(45, 0, 0, 90, 1, (0, 1, 0))