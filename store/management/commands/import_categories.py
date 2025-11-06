import requests
from django.core.management.base import BaseCommand
from store.models import Category

class Command(BaseCommand):
    help = 'Import product categories from DummyJSON API (新版結構)'

    def handle(self, *args, **kwargs):
        url = "https://dummyjson.com/products/categories"
        response = requests.get(url)
        data = response.json()

        # 驗證是否為列表
        if isinstance(data, list):
            self.stdout.write(self.style.SUCCESS(f"Found {len(data)} categories to import"))

            for item in data:
                # ✅ 現在 item 是一個 dict，包含 slug/name/url
                slug = item.get("slug")
                name = item.get("name")

                if not slug or not name:
                    self.stdout.write(self.style.WARNING(f"⚠️ Skipped invalid category: {item}"))
                    continue

                category, created = Category.objects.get_or_create(
                    slug=slug,
                    defaults={"name": name}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"✅ Created category: {name} ({slug})"))
                else:
                    self.stdout.write(self.style.WARNING(f"⚠️ Category already exists: {name} ({slug})"))

            self.stdout.write(self.style.SUCCESS("🎉 Categories import completed successfully!"))
        else:
            self.stdout.write(self.style.ERROR("❌ Unexpected API response format"))