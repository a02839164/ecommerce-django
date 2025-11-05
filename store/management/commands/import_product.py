import os
import requests
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.conf import settings
from store.models import Product, Category


class Command(BaseCommand):
    help = "Import products from DummyJSON API and download all images to local MEDIA_ROOT"

    def handle(self, *args, **kwargs):
        url = "https://dummyjson.com/products?limit=100"
        response = requests.get(url)
        data = response.json()

        products = data.get("products", [])
        self.stdout.write(self.style.SUCCESS(f"📦 Found {len(products)} products to import."))

        for item in products:
            try:
                category_slug = item.get("category")
                category = Category.objects.filter(slug=category_slug).first()
                if not category:
                    self.stdout.write(self.style.WARNING(f"⚠️ No category found for {category_slug}, skipping."))
                    continue

                # 建立唯一 slug
                base_slug = slugify(item["title"])
                slug = base_slug
                counter = 1
                while Product.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                # === 下載 thumbnail ===
                thumbnail_file = None
                thumbnail_url = item.get("thumbnail")
                if thumbnail_url:
                    try:
                        thumb_response = requests.get(thumbnail_url, timeout=10)
                        thumb_response.raise_for_status()
                        thumb_name = f"{slug}-thumb.jpg"
                        thumbnail_file = ContentFile(thumb_response.content, name=thumb_name)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"⚠️ Thumbnail download failed for {slug}: {e}"))

                # === 下載 images 陣列 ===
                downloaded_images = []
                for idx, img_url in enumerate(item.get("images", []), start=1):
                    try:
                        img_response = requests.get(img_url, timeout=10)
                        img_response.raise_for_status()
                        img_name = f"{slug}-{idx}.jpg"
                        file_path = os.path.join("product_image", img_name)

                        # 寫入本地 MEDIA_ROOT
                        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        with open(full_path, "wb") as f:
                            f.write(img_response.content)

                        downloaded_images.append(file_path)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"⚠️ Failed to download image {img_url}: {e}"))

                # === 建立商品 ===
                product = Product.objects.create(
                    category=category,
                    title=item["title"],
                    brand=item.get("brand", "un-branded"),
                    description=item.get("description", ""),
                    slug=slug,
                    price=item.get("price", 0.00),
                    discountpercentage=item.get("discountPercentage"),
                    stock=item.get("stock", 0),
                    sku=item.get("sku"),
                    weight=item.get("weight"),
                    dimensions=item.get("dimensions"),
                    warrantyinformation=item.get("warrantyInformation"),
                    shippinginformation=item.get("shippingInformation"),
                    returnpolicy=item.get("returnPolicy"),
                    image=downloaded_images,  # JSONField — 本地路徑清單
                )

                if thumbnail_file:
                    product.thumbnail.save(thumbnail_file.name, thumbnail_file, save=True)

                self.stdout.write(self.style.SUCCESS(f"✅ Imported: {product.title}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error importing {item.get('title')}: {e}"))

        self.stdout.write(self.style.SUCCESS("🎉 Products import completed successfully!"))