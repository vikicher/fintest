from datetime import date as date_cls
from decimal import Decimal

from django.utils import timezone

from currency.clients import NbuExchangeRateClient
from currency.exceptions import CurrencyRateUnavailable
from currency.models import ExchangeRate


class ExchangeRateSyncService:
    """Синхронізує курси валют НБУ за вказану дату у власну базу"""

    def __init__(self, client: NbuExchangeRateClient | None = None):
        self.client = client or NbuExchangeRateClient()

    def sync_for_date(self, target_date: date_cls) -> None:
        rates = self.client.fetch_rates(target_date)
        for item in rates:
            ExchangeRate.objects.update_or_create(
                currency_code=item["cc"],
                rate_date=target_date,
                defaults={"rate_to_uah": Decimal(str(item["rate"]))},
            )


class CurrencyConversionService:
    """Конвертація сум між валютами через гривню як опорну валюту"""

    @staticmethod
    def _rate_to_uah(currency_code: str, target_date: date_cls) -> Decimal:
        if currency_code == "UAH":
            return Decimal("1")

        rate = (
            ExchangeRate.objects
            .filter(currency_code=currency_code, rate_date__lte=target_date)
            .order_by("-rate_date")
            .first()
        )
        if rate is None:
            raise CurrencyRateUnavailable(currency_code)
        return rate.rate_to_uah

    @classmethod
    def convert(
        cls,
        amount: Decimal,
        from_code: str,
        to_code: str,
        target_date: date_cls | None = None,
    ) -> Decimal:
        target_date = target_date or timezone.localdate()

        if from_code == to_code:
            return amount

        amount_in_uah = amount * cls._rate_to_uah(from_code, target_date)
        return amount_in_uah / cls._rate_to_uah(to_code, target_date)
