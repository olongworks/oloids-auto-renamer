from unittest import TestCase

from oloids_auto_renamer.models.entities import DetectionRule
from oloids_auto_renamer.rules.detector import ToolDetector


class ToolDetectorTests(TestCase):
    def test_detects_matching_tool_by_priority(self) -> None:
        detector = ToolDetector(
            [
                DetectionRule(id=1, tool_name="Higgsfield", pattern=r"higgsfield", priority=20, is_active=True),
                DetectionRule(id=2, tool_name="Kling", pattern=r"kling", priority=10, is_active=True),
            ]
        )

        result = detector.detect("my_kling_render.mp4")

        self.assertEqual("Kling", result.tool_name)

    def test_detects_higgsfield_images(self) -> None:
        detector = ToolDetector(
            [
                DetectionRule(id=1, tool_name="Kling", pattern=r"kling", priority=10, is_active=True),
                DetectionRule(id=2, tool_name="Higgsfield", pattern=r"higgsfield|higgs[_ -]?field|higgs", priority=20, is_active=True),
            ]
        )

        result = detector.detect("higgsfield_portrait_01.webp")

        self.assertEqual("Higgsfield", result.tool_name)

    def test_returns_unknown_when_no_rule_matches(self) -> None:
        detector = ToolDetector([])

        result = detector.detect("clip_final.mp4")

        self.assertEqual("UNKNOWN", result.tool_name)
