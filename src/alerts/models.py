from django.conf import settings
from django.db import models

from catalog.models import Product


class PriceDropSubscription(models.Model):
    """Підписка користувача на сповіщення, якщо ціна товару опуститься нижче вказаної"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="price_alerts",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    threshold_price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="UAH")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    triggered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["product", "is_active"])]

    def __str__(self) -> str:
        return f"{self.user_id} -> {self.product_id} <= {self.threshold_price} {self.currency}"
