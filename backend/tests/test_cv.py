import sys
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from PIL import Image

from qaddir_api.config import DAMAGE_CLASSES, PART_CLASSES, Settings, Thresholds
from qaddir_api.cv import PreparedImage, UltralyticsCVPipeline, normalise_class_name


def settings(damage_path: Path, part_path: Path) -> Settings:
    return Settings(
        damage_model_path=damage_path,
        part_model_path=part_path,
        cv_confidence=0.2,
        cv_image_size=640,
        cv_device="cpu",
        prompt_path=Path("unused-prompt.md"),
        llm_api_key=None,
        llm_model=None,
        thresholds=Thresholds(None, None, None, None, None),
    )


class FakeModel:
    def __init__(self, names):
        # Ultralytics exposes `model.names` as {index: label}, with indices fixed
        # by training order. Accept a mapping verbatim so tests can reproduce a
        # real checkpoint; fall back to enumeration for call-sites passing a set.
        self.names = (
            dict(names)
            if isinstance(names, dict)
            else {index: name for index, name in enumerate(sorted(names))}
        )
        self.predict_calls = []

    def predict(self, image, **options):
        self.predict_calls.append((image, options))
        return [SimpleNamespace(boxes=None, names=self.names)]


class CVReadinessTests(TestCase):
    def test_readiness_rejects_missing_model_file(self):
        with TemporaryDirectory() as directory:
            damage_path = Path(directory) / "damage.pt"
            part_path = Path(directory) / "missing-part.pt"
            damage_path.touch()

            ready, detail = UltralyticsCVPipeline(settings(damage_path, part_path)).readiness()

            self.assertFalse(ready)
            self.assertIn(str(part_path), detail)

    def test_readiness_loads_models_and_validates_vocabularies(self):
        with TemporaryDirectory() as directory:
            damage_path = Path(directory) / "damage.pt"
            part_path = Path(directory) / "part.pt"
            damage_path.touch()
            part_path.touch()
            loaded_paths = []

            def yolo(path):
                loaded_paths.append(path)
                classes = DAMAGE_CLASSES if Path(path) == damage_path else PART_CLASSES
                return FakeModel(classes)

            with patch.dict(sys.modules, {"ultralytics": SimpleNamespace(YOLO=yolo)}):
                ready, detail = UltralyticsCVPipeline(settings(damage_path, part_path)).readiness()

            self.assertTrue(ready)
            self.assertEqual(loaded_paths, [str(damage_path), str(part_path)])
            self.assertIn("class vocabularies match", detail)

    def test_readiness_rejects_model_with_wrong_vocabulary(self):
        with TemporaryDirectory() as directory:
            damage_path = Path(directory) / "damage.pt"
            part_path = Path(directory) / "part.pt"
            damage_path.touch()
            part_path.touch()

            def yolo(path):
                classes = {"not_a_damage_class"} if Path(path) == damage_path else PART_CLASSES
                return FakeModel(classes)

            pipeline = UltralyticsCVPipeline(settings(damage_path, part_path))
            with patch.dict(sys.modules, {"ultralytics": SimpleNamespace(YOLO=yolo)}):
                ready, detail = pipeline.readiness()

            self.assertFalse(ready)
            self.assertIn("expected", detail)
            self.assertIsNone(pipeline._damage_model)
            self.assertIsNone(pipeline._part_model)

    def test_readiness_requires_explicit_inference_configuration_after_model_validation(self):
        with TemporaryDirectory() as directory:
            damage_path = Path(directory) / "damage.pt"
            part_path = Path(directory) / "part.pt"
            damage_path.touch()
            part_path.touch()
            incomplete = replace(settings(damage_path, part_path), cv_confidence=None)

            def yolo(path):
                classes = DAMAGE_CLASSES if Path(path) == damage_path else PART_CLASSES
                return FakeModel(classes)

            with patch.dict(sys.modules, {"ultralytics": SimpleNamespace(YOLO=yolo)}):
                ready, detail = UltralyticsCVPipeline(incomplete).readiness()

            self.assertFalse(ready)
            self.assertIn("models load and their class vocabularies match", detail)
            self.assertIn("QADDIR_CV_CONFIDENCE", detail)

    def test_inference_passes_explicit_ultralytics_options(self):
        with TemporaryDirectory() as directory:
            damage_path = Path(directory) / "damage.pt"
            part_path = Path(directory) / "part.pt"
            damage_path.touch()
            part_path.touch()
            pipeline = UltralyticsCVPipeline(settings(damage_path, part_path))
            damage_model = FakeModel(DAMAGE_CLASSES)
            part_model = FakeModel(PART_CLASSES)
            pipeline._damage_model = damage_model
            pipeline._part_model = part_model

            pipeline.infer(
                PreparedImage(
                    image=Image.new("RGB", (640, 640), "white"),
                    image_id="test.jpg",
                    usable=True,
                    quality_note=None,
                )
            )

            self.assertEqual(
                damage_model.predict_calls[0][1],
                {"conf": 0.2, "imgsz": 640, "device": "cpu", "verbose": False},
            )
            self.assertEqual(
                part_model.predict_calls[0][1],
                {
                    "conf": 0.2,
                    "imgsz": 640,
                    "device": "cpu",
                    "verbose": False,
                    "retina_masks": True,
                },
            )


# The trained damage checkpoint's real layout: indices fixed by training order,
# with three labels carrying display spacing rather than the documented snake_case.
DISPLAY_DAMAGE_NAMES = {
    0: "dent",
    1: "scratch",
    2: "crack",
    3: "glass shatter",
    4: "lamp broken",
    5: "tire flat",
}


class FakeTensor:
    def __init__(self, values):
        self._values = values

    def cpu(self):
        return self

    def tolist(self):
        return self._values


class FakeBoxes:
    """Minimal stand-in for Ultralytics `result.boxes`."""

    def __init__(self, rows):
        self.xyxy = FakeTensor([list(row[0]) for row in rows])
        self.conf = FakeTensor([row[1] for row in rows])
        self.cls = FakeTensor([row[2] for row in rows])


class ClassNameNormalisationTests(TestCase):
    def test_display_labels_map_to_documented_taxonomy(self):
        self.assertEqual(normalise_class_name("glass shatter"), "glass_shatter")
        self.assertEqual(normalise_class_name("lamp broken"), "lamp_broken")
        self.assertEqual(normalise_class_name("tire flat"), "tire_flat")

    def test_already_normalised_and_unknown_labels_pass_through(self):
        self.assertEqual(normalise_class_name("dent"), "dent")
        self.assertEqual(normalise_class_name("front_bumper"), "front_bumper")
        # Unknown labels are not coerced; they must reach the vocabulary check.
        self.assertEqual(normalise_class_name("frame bent"), "frame bent")

    def test_readiness_accepts_a_checkpoint_using_display_labels(self):
        with TemporaryDirectory() as directory:
            damage_path = Path(directory) / "damage.pt"
            part_path = Path(directory) / "part.pt"
            damage_path.touch()
            part_path.touch()

            def yolo(path):
                if Path(path) == damage_path:
                    return FakeModel(DISPLAY_DAMAGE_NAMES)
                return FakeModel(PART_CLASSES)

            with patch.dict(sys.modules, {"ultralytics": SimpleNamespace(YOLO=yolo)}):
                ready, detail = UltralyticsCVPipeline(settings(damage_path, part_path)).readiness()

            self.assertTrue(ready, detail)

    def test_readiness_still_rejects_an_unknown_label(self):
        names = dict(DISPLAY_DAMAGE_NAMES)
        names[6] = "frame bent"
        with TemporaryDirectory() as directory:
            damage_path = Path(directory) / "damage.pt"
            part_path = Path(directory) / "part.pt"
            damage_path.touch()
            part_path.touch()

            def yolo(path):
                if Path(path) == damage_path:
                    return FakeModel(names)
                return FakeModel(PART_CLASSES)

            pipeline = UltralyticsCVPipeline(settings(damage_path, part_path))
            with patch.dict(sys.modules, {"ultralytics": SimpleNamespace(YOLO=yolo)}):
                ready, detail = pipeline.readiness()

            self.assertFalse(ready)
            self.assertIn("frame bent", detail)
            self.assertIsNone(pipeline._damage_model)

    def test_extract_normalises_labels_by_class_index(self):
        # class_id 3 is "glass shatter" in the trained checkpoint.
        result = SimpleNamespace(
            names=DISPLAY_DAMAGE_NAMES,
            boxes=FakeBoxes(
                [
                    ((10.0, 20.0, 30.0, 40.0), 0.91, 3.0),
                    ((50.0, 60.0, 70.0, 80.0), 0.72, 0.0),
                ]
            ),
        )

        detections = UltralyticsCVPipeline._extract(result, "damage", "d", DAMAGE_CLASSES)

        self.assertEqual([item.class_name for item in detections], ["glass_shatter", "dent"])
        self.assertEqual([item.id for item in detections], ["d1", "d2"])
