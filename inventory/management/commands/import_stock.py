import csv
import os
from django.core.management.base import BaseCommand
from store.models import Product
from inventory.models import InventoryLog

class Command(BaseCommand):
    help = "Import product stock from CSV and update inventory"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="CSV file path")

    def handle(self, *args, **options):
        csv_file = options["csv_file"]
        filepath = os.path.join(os.getcwd(), csv_file)

        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f"File not found: {filepath}"))
            return

        updated = 0
        errors = []

        with open(filepath, newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                product_id = row["id"]
                new_stock = int(row["stock"])

                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    errors.append(f"Product ID {product_id} not found")
                    continue

                old_stock = product.stock
                diff = new_stock - old_stock

                if diff != 0:
                    product.stock = new_stock
                    product.save()

                    InventoryLog.objects.create(
                        product=product,
                        quantity=diff,
                        action="BULK_UPDATE",
                        note=f"Bulk CSV import: {old_stock} → {new_stock}"
                    )

                    updated += 1

        self.stdout.write(self.style.SUCCESS(f"Updated {updated} items"))
        if errors:
            self.stdout.write(self.style.ERROR("\n".join(errors)))
