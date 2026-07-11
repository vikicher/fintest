from datetime import date as date_cls

from django.utils import timezone

from alerts.models import PriceDropSubscription
from catalog.models import ProductDailyStat
from currency.services import CurrencyConversionService


class PriceAlertService:
    """Перевіряє активні підписки та ставить у чергу лист, якщо ціна опустилась нижче порогу"""

    @staticmethod
    def check_and_notify(target_date: date_cls | None = None) -> None:
        target_date = target_date or timezone.localdate()

        subscriptions = (
            PriceDropSubscription.objects
            .filter(is_active=True)
            .select_related("user", "product")
        )

        stats_by_product = {
            stat.product_id: stat
            for stat in ProductDailyStat.objects.filter(date=target_date)
        }

        for subscription in subscriptions:
            stat = stats_by_product.get(subscription.product_id)
            if stat is None:
                continue

            current_min_price = CurrencyConversionService.convert(
                stat.min_price, "USD", subscription.currency, target_date,
            )

            if current_min_price <= subscription.threshold_price:
                PriceAlertService._trigger(subscription, current_min_price)

    @staticmethod
    def _trigger(subscription: PriceDropSubscription, current_price) -> None:
        from alerts.tasks import send_price_drop_email

        send_price_drop_email.delay(subscription.id, str(current_price))

        subscription.is_active = False
        subscription.triggered_at = timezone.now()
        subscription.save(update_fields=["is_active", "triggered_at"])