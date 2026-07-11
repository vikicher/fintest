from django.db import models


class Store(models.Model):
    class Code(models.TextChoices):
        DUMMYJSON = "dummyjson", "DummyJSON"
        FAKESTORE = "fakestoreapi", "FakeStoreAPI"

    code = models.CharField(max_length=20, choices=Code.choices, unique=True)
    name = models.CharField(max_length=100)
    base_currency = models.CharField(max_length=3, default="USD")
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    """Єдиний (агрегований) товар, до якого може належати кілька пропозицій з різних магазинів"""

    title = models.CharField(max_length=512)
    normalized_title = models.CharField(max_length=512, db_index=True)  # для зіставлення при синхронізації
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title


class StoreProduct(models.Model):
    """Конкретна пропозиція товару в конкретному магазині"""

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="offers")
    external_id = models.CharField(max_length=100)  # id товару в API магазину
    title_raw = models.CharField(max_length=512)
    is_available = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("store", "external_id")
        indexes = [models.Index(fields=["product"])]

    def __str__(self) -> str:
        return f"{self.store.code}: {self.title_raw}"


class PriceRecord(models.Model):
    """Ціна конкретної пропозиції на конкретну дату (нативна валюта — зазвичай USD)"""

    store_product = models.ForeignKey(StoreProduct, on_delete=models.CASCADE, related_name="price_records")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    price_date = models.DateField()
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("store_product", "price_date")
        indexes = [models.Index(fields=["store_product", "-price_date"])]

    def __str__(self) -> str:
        return f"{self.store_product_id} @ {self.price_date}: {self.price} {self.currency}"


class ProductDailyStat(models.Model):
    """Попередньо розрахована агрегація по товару за день — використовується для списку/тренда"""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="daily_stats")
    date = models.DateField()
    min_price = models.DecimalField(max_digits=12, decimal_places=2)
    max_price = models.DecimalField(max_digits=12, decimal_places=2)
    avg_price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")

    class Meta:
        unique_together = ("product", "date")
        indexes = [models.Index(fields=["product", "-date"])]

    def __str__(self) -> str:
        return f"{self.product_id} @ {self.date}"