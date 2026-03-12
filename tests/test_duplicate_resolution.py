from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from oloids_auto_renamer.models.entities import ProjectPreset
from oloids_auto_renamer.services.naming_service import NamingService
from oloids_auto_renamer.services.processing_service import FileProcessingService


class DuplicateResolutionTests(TestCase):
    def test_resolve_unique_path_increments_sequence(self) -> None:
        service = NamingService()

        with TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            existing = directory / "0311_oloids_001.mp4"
            existing.write_bytes(b"data")

            resolved = service.resolve_unique_path(
                directory,
                pattern="{mmdd}_{project}_{seq}",
                project="oloids",
                tool="Kling",
                asset_type="video",
                extension=".mp4",
                now=datetime(2026, 3, 11),
            )

            self.assertEqual("0311_oloids_002.mp4", resolved.name)

    def test_route_kling_videos_to_dated_video_folder(self) -> None:
        service = FileProcessingService.__new__(FileProcessingService)
        project = ProjectPreset(
            id=1,
            name="Kling Project",
            output_path=r"D:\fallback",
            naming_pattern="{mmdd}_{project}_{seq}",
            default_tool="Kling",
            is_active=True,
            fallback_unsorted=True,
        )

        destination = FileProcessingService._resolve_destination_dir(service, Path("clip.mp4"), "Kling", project, datetime(2026, 3, 11))

        self.assertEqual(Path(r"D:\OLOIDS\OAR-Video\[0311]"), destination)

    def test_route_higgsfield_images_to_dated_image_folder(self) -> None:
        service = FileProcessingService.__new__(FileProcessingService)
        project = ProjectPreset(
            id=1,
            name="Kling Project",
            output_path=r"D:\fallback",
            naming_pattern="{mmdd}_{project}_{seq}",
            default_tool="Kling",
            is_active=True,
            fallback_unsorted=True,
        )

        destination = FileProcessingService._resolve_destination_dir(service, Path("portrait.webp"), "Higgsfield", project, datetime(2026, 3, 11))

        self.assertEqual(Path(r"D:\OLOIDS\OAR-image\[0311]"), destination)
