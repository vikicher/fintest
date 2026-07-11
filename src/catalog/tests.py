from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status


pytestmark = pytest.mark.django_db


class TestProductListView:
    @pytest.fixture(autouse=True)
    def setup(self, usd_rate, make_product_with_stats):
        self.url = reverse("product-list")
        self.rising_product = make_product_with_stats("Rising Product", Decimal("110"), Decimal("100"))
        self.falling_product = make_product_with_stats("Falling Product", Decimal("90"), Decimal("100"))
        self.stable_product = make_product_with_stats("Stable Product", Decimal("100.30"), Decimal("100"))

    def test_list_returns_price_range_and_trend(self, api_client):
        response = api_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        titles_to_trend = {item["title"]: item["trend"] for item in response.data["results"]}

        assert titles_to_trend["Rising Product"] == "up"
        assert titles_to_trend["Falling Product"] == "down"
        assert titles_to_trend["Stable Product"] == "same"

    def test_list_default_currency_is_uah_and_converts_price(self, api_client):
        response = api_client.get(self.url)

        item = next(i for i in response.data["results"] if i["title"] == "Stable Product")
        assert item["currency"] == "UAH"
        assert Decimal(item["price_from"]) == Decimal("95.30") * Decimal("41.00")

    def test_list_can_request_prices_in_usd(self, api_client):
        response = api_client.get(self.url, {"currency": "USD"})

        item = next(i for i in response.data["results"] if i["title"] == "Stable Product")
        assert item["currency"] == "USD"
        assert Decimal(item["price_from"]) == Decimal("95.30")

    def test_list_sort_by_price_ascending(self, api_client):
        response = api_client.get(self.url, {"sort": "price", "order": "asc"})

        titles = [item["title"] for item in response.data["results"]]
        assert titles[0] == "Falling Product"

    def test_list_sort_by_trend(self, api_client):
        response = api_client.get(self.url, {"sort": "trend", "order": "asc"})

        titles = [item["title"] for item in response.data["results"]]
        assert titles == ["Falling Product", "Stable Product", "Rising Product"]


class TestProductDetailView:
    @pytest.fixture(autouse=True)
    def setup(self, usd_rate, make_product_with_stats):
        self.product = make_product_with_stats("Test Product", Decimal("100"), Decimal("100"))
        self.product.description = "Опис товару"
        self.product.save(update_fields=["description"])

    def test_detail_returns_title_description_and_price_range(self, api_client):
        url = reverse("product-detail", args=[self.product.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Test Product"
        assert response.data["description"] == "Опис товару"
        assert response.data["price_from"] is not None
        assert response.data["price_to"] is not None

    def test_detail_returns_404_for_unknown_product(self, api_client):
        url = reverse("product-detail", args=[999999])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestProductOffersView:
    @pytest.fixture(autouse=True)
    def setup(self, usd_rate, make_product_with_stats):
        self.product = make_product_with_stats("Test Product", Decimal("100"), Decimal("100"))

    def test_offers_returns_price_per_store(self, api_client):
        url = reverse("product-offers", args=[self.product.id])
        response = api_client.get(url, {"currency": "USD"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

        store_names = {item["store"] for item in response.data}
        assert store_names == {"DummyJSON", "FakeStoreAPI"}


class TestProductPriceHistoryView:
    @pytest.fixture(autouse=True)
    def setup(self, usd_rate, today, make_product_with_stats):
        self.today = today
        self.product = make_product_with_stats("Test Product", Decimal("100"), Decimal("100"))

    def test_price_history_groups_points_by_date(self, api_client):
        url = reverse("product-price-history", args=[self.product.id])
        response = api_client.get(url, {"currency": "USD", "days": 5})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

        today_point = next(p for p in response.data if str(p["date"]) == str(self.today))
        assert "by_store" in today_point
        assert len(today_point["by_store"]) == 2
        assert "average" in today_point