import requests
from django.core.management.base import BaseCommand
from store.models import Category

class Command(BaseCommand):

    help = 'Import product categories from DummyJSON API'

    def handle(self, *args, **kwargs):
        # DummyJSON API 的分類端點
        url = "https://dummyjson.com/products/categories"
        response = requests.get(url)
        data = response.json()


        if isinstance(data, list):
            self.stdout.write(self.style.SUCCESS(f"Found {len(data)} categories to import"))

            for item in data:

                name = item.get("name")
                slug = item.get("slug")

                category, created =Category.objects.get_or_create(
                    slug=slug,
                    defaults={"name":name}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f" Created category: {name} ({slug}) "))
                else:
                    self.stdout.write(self.style.WARNING(f" Category already exists: {name} ({slug}) "))

            self.stdout.write(self.style.SUCCESS("Categories import completed successfully!"))