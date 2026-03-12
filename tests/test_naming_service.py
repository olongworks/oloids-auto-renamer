from datetime import datetime
from unittest import TestCase

from oloids_auto_renamer.services.naming_service import NamingService


class NamingServiceTests(TestCase):
    def test_render_pattern_replaces_tokens(self) -> None:
        service = NamingService()

        rendered = service.render_pattern(
            "{mmdd}_{project}_{seq}",
            project="oloids tiger",
            tool="Kling",
            asset_type="video",
            sequence=3,
            now=datetime(2026, 3, 11),
        )

        self.assertEqual("0311_oloids_tiger_003", rendered)
