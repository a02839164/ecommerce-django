from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.conf import settings
from pathlib import Path
import os

class Command(BaseCommand):
    help = "Upload all files from local MEDIA_ROOT to Google Cloud Storage"

    def handle(self, *args, **options):
        media_root = getattr(settings, "MEDIA_ROOT", None)
        if not media_root or not os.path.exists(media_root):
            self.stdout.write(self.style.ERROR("❌ MEDIA_ROOT not found or invalid"))
            return

        self.stdout.write(self.style.WARNING(f"🚀 Start uploading from: {media_root}"))
        uploaded, failed = 0, 0

        for root, dirs, files in os.walk(media_root):
            for filename in files:
                local_path = Path(root) / filename
                relative_path = local_path.relative_to(media_root).as_posix()

                try:
                    with open(local_path, "rb") as f:
                        default_storage.save(relative_path, f)
                    uploaded += 1
                    self.stdout.write(self.style.SUCCESS(f"✅ Uploaded: {relative_path}"))
                except Exception as e:
                    failed += 1
                    self.stdout.write(self.style.ERROR(f"❌ Failed {relative_path}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\n✅ Upload complete: {uploaded} success, {failed} failed"))
