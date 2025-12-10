from django.core.management.base import BaseCommand
from datetime import timedelta
from django.utils import timezone
from django.db import transaction

from payment.models import Order
from inventory.services import InventoryService


class Command(BaseCommand):
    help = "Release expired reserved stock for PENDING orders"

    def add_arguments(self, parser):
        parser.add_argument(
            "--minutes",
            type=int,
            default=15,
            help="Expire orders older than N minutes (default: 15)",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only show what would be released (no data will be changed)",
        )

    def handle(self, *args, **options):
        minutes = options["minutes"]
        dry_run = options["dry_run"]

        deadline = timezone.now() - timedelta(minutes=minutes)

        qs = Order.objects.filter(
            payment_status="PENDING",
            date_ordered__lt=deadline
        )

        total = qs.count()
        released_orders = []

        self.stdout.write(
            f"🔍 Found {total} expired PENDING orders (>{minutes} minutes)"
        )

        for order in qs:
            try:
                with transaction.atomic():
                    order.refresh_from_db()

                    # 再保險確認一次狀態
                    if order.payment_status != "PENDING":
                        continue

                    if dry_run:
                        released_orders.append(order.id)
                        self.stdout.write(
                            f"[DRY-RUN] Would release Order #{order.id}"
                        )
                        continue

                    # ✅ 正式釋放庫存
                    InventoryService.release_stock(order)

                    released_orders.append(order.id)

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Released stock for Order #{order.id}"
                        )
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Failed to release Order #{order.id}: {e}"
                    )
                )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY-RUN DONE] Would release {len(released_orders)} orders"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"🎉 DONE! Released {len(released_orders)} orders"
                )
            )
