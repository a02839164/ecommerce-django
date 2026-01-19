import csv
import os
from django.core.management.base import BaseCommand
from store.models import Product



class Command(BaseCommand):
    help = "Export all product stock to CSV"

    def handle(self, *args, **kwargs):
        filename = "products-stock.csv"
        filepath = os.path.join(os.getcwd(), filename)

        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["id", "title", "stock"])

            for p in Product.objects.all().only("id", "title", "stock"):
                writer.writerow([p.id, p.title, p.stock])

        self.stdout.write(self.style.SUCCESS(f"Exported → {filepath}"))
