"""Filename pattern rendering and duplicate-safe resolution."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*]+')


class NamingService:
    """Render filenames from variables and avoid collisions."""

    def sanitize_token(self, value: str) -> str:
        clean = INVALID_FILENAME_CHARS.sub("_", value.strip())
        clean = re.sub(r"\s+", "_", clean)
        return clean.strip("._") or "untitled"

    def render_pattern(
        self,
        pattern: str,
        *,
        project: str,
        tool: str,
        asset_type: str,
        sequence: int,
        version: int = 1,
        now: datetime | None = None,
    ) -> str:
        current = now or datetime.now()
        context = {
            "project": self.sanitize_token(project),
            "tool": self.sanitize_token(tool.lower()),
            "yyyymmdd": current.strftime("%Y%m%d"),
            "mmdd": current.strftime("%m%d"),
            "seq": f"{sequence:03d}",
            "version": f"v{version:02d}",
            "assetType": self.sanitize_token(asset_type),
        }
        rendered = pattern
        for key, value in context.items():
            rendered = rendered.replace(f"{{{key}}}", value)
        return self.sanitize_token(rendered)

    def resolve_unique_path(
        self,
        directory: Path,
        *,
        pattern: str,
        project: str,
        tool: str,
        asset_type: str,
        extension: str,
        now: datetime | None = None,
    ) -> Path:
        directory.mkdir(parents=True, exist_ok=True)

        for sequence in range(1, 10000):
            base_name = self.render_pattern(
                pattern,
                project=project,
                tool=tool,
                asset_type=asset_type,
                sequence=sequence,
                version=1,
                now=now,
            )
            candidate = directory / f"{base_name}{extension.lower()}"
            if not candidate.exists():
                return candidate

            for version in range(2, 100):
                versioned_name = self.render_pattern(
                    f"{pattern}_{{version}}",
                    project=project,
                    tool=tool,
                    asset_type=asset_type,
                    sequence=sequence,
                    version=version,
                    now=now,
                )
                versioned_candidate = directory / f"{versioned_name}{extension.lower()}"
                if not versioned_candidate.exists():
                    return versioned_candidate

        raise RuntimeError("Unable to resolve a unique filename.")
