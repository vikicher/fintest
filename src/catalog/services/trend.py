from datetime import date as date_cls, timedelta
from decimal import Decimal

from django.db.models import Avg

from catalog.choices import Trend
from catalog.models import ProductDailyStat

TREND_THRESHOLD_PERCENT = Decimal("1")  # поріг "шуму", нижче якого вважаємо "на тому ж рівні"
TREND_WINDOW_DAYS = 30


class TrendService:
    """Визначає тренд ціни товару порівняно із середньою ціною за попередні 30 днів"""

    @staticmethod
    def calculate(product_id: int, target_date: date_cls) -> tuple[str, Decimal | None]:
        today_stat = (
            ProductDailyStat.objects
            .filter(product_id=product_id, date=target_date)
            .first()
        )
        if today_stat is None:
            return Trend.SAME, None

        window_start = target_date - timedelta(days=TREND_WINDOW_DAYS)
        avg_30d = (
            ProductDailyStat.objects
            .filter(product_id=product_id, date__gte=window_start, date__lt=target_date)
            .aggregate(value=Avg("avg_price"))["value"]
        )

        if not avg_30d:
            return Trend.SAME, None

        delta_percent = (today_stat.avg_price - avg_30d) / avg_30d * 100

        if delta_percent > TREND_THRESHOLD_PERCENT:
            return Trend.UP, delta_percent
        if delta_percent < -TREND_THRESHOLD_PERCENT:
            return Trend.DOWN, delta_percent
        return Trend.SAME, delta_percent