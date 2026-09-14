from unittest import TestCase

from qaddir_api.matching import Box, associate_by_overlap, damage_coverage
from qaddir_api.schemas import VisualDetection


class MatchingTests(TestCase):
    def test_damage_coverage_uses_damage_as_denominator(self):
        self.assertEqual(damage_coverage(Box(0, 0, 10, 10), Box(0, 0, 5, 10)), 0.5)

    def test_association_preserves_competing_parts(self):
        detections = [
            VisualDetection(
                id="d1", kind="damage", class_name="dent", confidence=0.9, bbox=(0, 0, 10, 10)
            ),
            VisualDetection(
                id="p1", kind="part", class_name="front_door", confidence=0.9, bbox=(0, 0, 6, 10)
            ),
            VisualDetection(
                id="p2", kind="part", class_name="back_door", confidence=0.8, bbox=(5, 0, 10, 10)
            ),
        ]
        association = associate_by_overlap(detections)[0]
        self.assertEqual(association.part_id, "p1")
        self.assertEqual(association.confidence, 0.6)
        self.assertEqual(association.alternatives[0].part_id, "p2")


if __name__ == "__main__":
    import unittest

    unittest.main()
