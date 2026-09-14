from unittest import TestCase

from qaddir_api.report_guard import UnsafeReportError, validate_report
from qaddir_api.schemas import CVRecord


RECORD = CVRecord.model_validate(
    {
        "image": {"id": "test.jpg", "usable": True, "quality_note": None},
        "damage_detections": [{"id": "d1", "class": "dent", "confidence": 0.9}],
        "part_detections": [{"id": "p1", "class": "front_door", "confidence": 0.8}],
        "associations": [
            {"damage_id": "d1", "part_id": "p1", "confidence": 0.8, "alternatives": []}
        ],
    }
)


class ReportGuardTests(TestCase):
    def test_grounded_report_passes(self):
        validate_report(
            "A dent was detected on the front door. This is not an assessment of severity, repair requirements or cost.",
            RECORD,
        )

    def test_invented_part_fails(self):
        with self.assertRaises(UnsafeReportError):
            validate_report("A dent was detected on the front bumper.", RECORD)

    def test_repair_language_fails(self):
        with self.assertRaises(UnsafeReportError):
            validate_report("The front door requires repair.", RECORD)


if __name__ == "__main__":
    import unittest

    unittest.main()
