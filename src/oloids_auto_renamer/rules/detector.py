"""Regex-based source tool detection."""

from __future__ import annotations

import re
from dataclasses import dataclass

from oloids_auto_renamer.models.entities import DetectionRule


@dataclass(slots=True)
class MatchResult:
    tool_name: str
    matched_pattern: str | None = None


class ToolDetector:
    """Detect a source tool from filename patterns."""

    def __init__(self, rules: list[DetectionRule]) -> None:
        self.rules = sorted((rule for rule in rules if rule.is_active), key=lambda item: item.priority)

    def detect(self, filename: str) -> MatchResult:
        for rule in self.rules:
            if re.search(rule.pattern, filename, re.IGNORECASE):
                return MatchResult(tool_name=rule.tool_name, matched_pattern=rule.pattern)
        return MatchResult(tool_name="UNKNOWN", matched_pattern=None)
