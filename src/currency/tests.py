from decimal import Decimal
from unittest.mock import patch

import pytest

from currency.exceptions import CurrencyRateUnavailable
from currency.models import ExchangeRate
from currency.services import ExchangeRateSyncService, CurrencyConversionService


pytestmark = pytest.mark.django_db


class TestExchangeRateSyncService:
    @patch("currency.clients.NbuExchangeRateClient.fetch_rates")
    def test_sync_creates_exchange_rates(self, mocked_fetch_rates, today):
        mocked_fetch_rates.return_value = [
            {"cc": "USD", "rate": 41.25},
            {"cc": "EUR", "rate": 44.10},
        ]

        ExchangeRateSyncService().sync_for_date(today)

        assert ExchangeRate.objects.filter(currency_code="USD", rate_date=today).exists()
        assert ExchangeRate.objects.get(currency_code="USD", rate_date=today).rate_to_uah == Decimal("41.25")


class TestCurrencyConversionService:
    def test_convert_same_currency_returns_same_amount(self, usd_rate, today):
        result = CurrencyConversionService.convert(Decimal("100"), "USD", "USD", today)
        assert result == Decimal("100")

    def test_convert_usd_to_uah(self, usd_rate, today):
        result = CurrencyConversionService.convert(Decimal("10"), "USD", "UAH", today)
        assert result == Decimal("410.00")

    def test_convert_raises_when_rate_missing(self, usd_rate, today):
        with pytest.raises(CurrencyRateUnavailable):
            CurrencyConversionService.convert(Decimal("10"), "EUR", "UAH", today)