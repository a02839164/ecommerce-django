import requests
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from store.models import Product, Category


class Command(BaseCommand):
    help = "Import products from DummyJSON API using existing GCS images (no upload)"

    def handle(self, *args, **kwargs):
        # 來源 API
        url = "https://dummyjson.com/products?limit=100"
        response = requests.get(url)
        data = response.json()

        products = data.get("products", [])
        self.stdout.write(self.style.SUCCESS(f"📦 Found {len(products)} products to import."))

        for item in products:
            try:
                # 取得分類
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

                # === 建立圖片欄位 ===
                # ✅ 假設你的 bucket 名稱是 buyria-media
                bucket_url = "https://storage.googleapis.com/buyria-media"

                # 1️⃣ Thumbnail：product_image/<slug>-thumb.jpg
                thumbnail_path = f"product_image/{slug}-thumb.jpg"

                # 2️⃣ 多圖陣列（假設 GCS 命名與 slug 對應，如 slug-1.jpg、slug-2.jpg...）
                image_list = []
                for idx, img_url in enumerate(item.get("images", []), start=1):
                    image_list.append(f"{bucket_url}/product_image/{slug}-{idx}.jpg")

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
                    thumbnail=thumbnail_path,  # ✅ GCS 相對路徑
                    image=image_list,          # ✅ JSONField → GCS 完整 URL
                )

                self.stdout.write(self.style.SUCCESS(f"✅ Imported: {product.title}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error importing {item.get('title')}: {e}"))

        self.stdout.write(self.style.SUCCESS("🎉 Products import completed successfully!"))