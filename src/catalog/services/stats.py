from datetime import date as date_cls

from django.db.models import Min, Max, Avg

from catalog.models import PriceRecord, ProductDailyStat


class StatsCalculationService:
    """Будує ProductDailyStat за вказану дату по всіх PriceRecord цієї дати"""

    @staticmethod
    def calculate_for_date(target_date: date_cls) -> None:
        aggregates = (
            PriceRecord.objects
            .filter(price_date=target_date)
            .values("store_product__product_id")
            .annotate(min_p=Min("price"), max_p=Max("price"), avg_p=Avg("price"))
        )

        for row in aggregates:
            ProductDailyStat.objects.update_or_create(
                product_id=row["store_product__product_id"],
                date=target_date,
                defaults={
                    "min_price": row["min_p"],
                    "max_price": row["max_p"],
                    "avg_price": row["avg_p"],
                    "currency": "USD",
                },
            )