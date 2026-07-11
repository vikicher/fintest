from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from catalog.models import Store, Product, StoreProduct, PriceRecord, ProductDailyStat
from currency.models import ExchangeRate
from users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="user@example.com", password="strong-password-123")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(email="other@example.com", password="strong-password-123")


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def today():
    return timezone.localdate()


@pytest.fixture
def usd_rate(db, today):
    return ExchangeRate.objects.create(currency_code="USD", rate_to_uah=Decimal("41.00"), rate_date=today)


@pytest.fixture
def store_a(db):
    return Store.objects.create(code=Store.Code.DUMMYJSON, name="DummyJSON")


@pytest.fixture
def store_b(db):
    return Store.objects.create(code=Store.Code.FAKESTORE, name="FakeStoreAPI")


@pytest.fixture
def make_product_with_stats(db, today, store_a, store_b):
    """Фабрика: створює товар із пропозиціями у двох магазинах, ціною на сьогодні
    і історією ProductDailyStat за попередні 30 днів."""

    def _make(title: str, today_avg: Decimal, past_avg: Decimal) -> Product:
        product = Product.objects.create(title=title, normalized_title=title.lower())

        store_product_a = StoreProduct.objects.create(
            store=store_a, product=product, external_id=f"{title}-a", title_raw=title,
        )
        store_product_b = StoreProduct.objects.create(
            store=store_b, product=product, external_id=f"{title}-b", title_raw=title,
        )

        PriceRecord.objects.create(
            store_product=store_product_a, price=today_avg - Decimal("5"),
            currency="USD", price_date=today,
        )
        PriceRecord.objects.create(
            store_product=store_product_b, price=today_avg + Decimal("5"),
            currency="USD", price_date=today,
        )

        ProductDailyStat.objects.create(
            product=product, date=today,
            min_price=today_avg - Decimal("5"), max_price=today_avg + Decimal("5"),
            avg_price=today_avg, currency="USD",
        )

        for days_ago in range(1, 31):
            ProductDailyStat.objects.create(
                product=product,
                date=today - timezone.timedelta(days=days_ago),
                min_price=past_avg, max_price=past_avg, avg_price=past_avg, currency="USD",
            )

        return product

    return _make