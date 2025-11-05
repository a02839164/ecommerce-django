from django.core.management.base import BaseCommand
from store.models import Product, Category
from faker import Faker
import random
from tqdm import tqdm
from django.utils.text import slugify
import uuid

class Command(BaseCommand):
    help = "Generate fake product data"

    def add_arguments(self, parser):
        parser.add_argument('count', type=int, help='Number of fake products to create')

    def handle(self, *args, **kwargs):
        fake = Faker()
        count = kwargs['count']
        categories = list(Category.objects.all())

        if not categories:
            self.stdout.write(self.style.ERROR('⚠️ No categories found! Please create some first.'))
            return

        batch_size = 10000
        products = []

        for i in tqdm(range(count), desc="Generating fake products"):
            title = fake.sentence(nb_words=3)
            slug = f"{slugify(title)}-{uuid.uuid4().hex[:8]}"  # ✅ 唯一 slug
            products.append(Product(
                title=title,
                slug=slug,
                description=fake.text(max_nb_chars=200),
                price=round(random.uniform(10, 1000), 2),
                category=random.choice(categories),
                is_fake=True,
            ))

            # ✅ 每滿 1000 筆就立即寫入資料庫
            if len(products) >= batch_size:
                Product.objects.bulk_create(products, batch_size=batch_size)
                products.clear()  # 清空記憶體

        # ✅ 最後剩下的不滿 1000 筆也要寫入
        if products:
            Product.objects.bulk_create(products, batch_size=batch_size)

        self.stdout.write(self.style.SUCCESS(f'✅ Successfully created {count} fake products!'))