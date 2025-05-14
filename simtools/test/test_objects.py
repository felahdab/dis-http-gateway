from twisted.trial import unittest
from simtools.objects import Missile
from opendis.dis7 import EntityID, EntityType

class missileTestCase(unittest.TestCase):
    def setUp(self):
        entity_id = EntityID(1, 20, 300)
        entity_type = EntityType(2, 6, 71, 1, 1, 4, 0)
        initial_position = [43, 5, 5]
        course = 230
        speed = 318
        maxrange = 10
        current_time = 1747084972
        timestamp = 1747084949
        weapon_flight_time = 125.78616352201257
        self.missile = Missile(entity_id, entity_type, None, initial_position, course, speed, maxrange, timestamp, current_time, weapon_flight_time)
    
    def test_advance_north(self):
        self.missile.course = 0 
        new_pos = self.missile.advance(60)
        self.assertGreater(new_pos[0], self.missile.current_position[0])
        self.assertAlmostEqual(new_pos[1], self.missile.current_position[1], places=4)

    def test_advance_east(self):
        self.missile.course = 90 
        new_pos = self.missile.advance(60)
        self.assertGreater(new_pos[1], self.missile.current_position[1])
        self.assertAlmostEqual(new_pos[0], self.missile.current_position[0], places=4)

    def test_advance_south(self):
        self.missile.course = 180
        new_pos = self.missile.advance(60)
        self.assertLess(new_pos[0], self.missile.current_position[0])

    def test_advance_west(self):
        self.missile.course = 270
        new_pos = self.missile.advance(60)
        self.assertLess(new_pos[1], self.missile.current_position[1])

    def test_advance_northeast(self):
        self.missile.course = 45
        new_pos = self.missile.advance(60)
        self.assertGreater(new_pos[0], self.missile.current_position[0])
        self.assertGreater(new_pos[1], self.missile.current_position[1])

    def test_no_movement_when_zero_seconds(self):
        new_pos = self.missile.advance(0)
        self.assertEqual(new_pos, self.missile.current_position)