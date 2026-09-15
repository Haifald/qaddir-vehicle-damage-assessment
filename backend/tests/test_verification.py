from unittest import TestCase

from qaddir_api.config import Thresholds
from qaddir_api.schemas import CVRecord
from qaddir_api.verification import verify_record


CALIBRATED = Thresholds(
    damage_report=0.4,
    damage_hedge=0.7,
    part_report=0.5,
    association_state=0.6,
    association_ambiguity=0.1,
)


def record(**overrides):
    value = {
        "image": {"id": "test.jpg", "usable": True, "quality_note": None},
        "damage_detections": [{"id": "d1", "class": "dent", "confidence": 0.9}],
        "part_detections": [{"id": "p1", "class": "front_door", "confidence": 0.8}],
        "associations": [
            {"damage_id": "d1", "part_id": "p1", "confidence": 0.8, "alternatives": []}
        ],
    }
    value.update(overrides)
    return CVRecord.model_validate(value)


class VerificationTests(TestCase):
    def test_valid_record_is_verified(self):
        result = verify_record(record(), CALIBRATED)
        self.assertEqual(result.status, "verified")
        self.assertTrue(result.llm_eligible)

    def test_low_confidence_requires_manual_review_and_blocks_llm(self):
        result = verify_record(
            record(
                damage_detections=[{"id": "d1", "class": "dent", "confidence": 0.2}]
            ),
            CALIBRATED,
        )
        self.assertEqual(result.status, "manual_review")
        self.assertFalse(result.llm_eligible)
        self.assertIn("low_damage_confidence", {issue.code for issue in result.issues})

    def test_hedge_band_requires_manual_review_and_blocks_llm(self):
        result = verify_record(
            record(
                damage_detections=[{"id": "d1", "class": "dent", "confidence": 0.5}]
            ),
            CALIBRATED,
        )
        self.assertEqual(result.status, "manual_review")
        self.assertFalse(result.llm_eligible)
        self.assertIn("damage_confidence_hedge_band", {issue.code for issue in result.issues})

    def test_ambiguous_association_requires_manual_review_and_blocks_llm(self):
        result = verify_record(
            record(
                part_detections=[
                    {"id": "p1", "class": "front_door", "confidence": 0.8},
                    {"id": "p2", "class": "back_door", "confidence": 0.8},
                ],
                associations=[
                    {
                        "damage_id": "d1",
                        "part_id": "p1",
                        "confidence": 0.8,
                        "alternatives": [{"part_id": "p2", "confidence": 0.75}],
                    }
                ],
            ),
            CALIBRATED,
        )
        self.assertEqual(result.status, "manual_review")
        self.assertFalse(result.llm_eligible)
        self.assertIn("ambiguous_part_association", {issue.code for issue in result.issues})

    def test_unknown_class_is_rejected_before_llm(self):
        result = verify_record(
            record(
                damage_detections=[{"id": "d1", "class": "rust", "confidence": 0.9}]
            ),
            CALIBRATED,
        )
        self.assertEqual(result.status, "rejected")
        self.assertFalse(result.llm_eligible)

    def test_contradictory_association_is_rejected(self):
        result = verify_record(
            record(
                damage_detections=[
                    {"id": "d1", "class": "tire_flat", "confidence": 0.9}
                ]
            ),
            CALIBRATED,
        )
        self.assertEqual(result.status, "rejected")
        self.assertIn("contradictory_association", {issue.code for issue in result.issues})

    def test_uncalibrated_thresholds_disable_llm(self):
        result = verify_record(record(), Thresholds(None, None, None, None, None))
        self.assertEqual(result.status, "manual_review")
        self.assertFalse(result.llm_eligible)


if __name__ == "__main__":
    import unittest

    unittest.main()
