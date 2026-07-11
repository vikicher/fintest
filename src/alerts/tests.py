from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status

from alerts.models import PriceDropSubscription
from catalog.models import Store, Product, StoreProduct, PriceRecord, ProductDailyStat


pytestmark = pytest.mark.django_db


@pytest.fixture
def product_with_today_stat(today):
    store = Store.objects.create(code=Store.Code.DUMMYJSON, name="DummyJSON")
    product = Product.objects.create(title="Test Product", normalized_title="test product")

    store_product = StoreProduct.objects.create(
        store=store, product=product, external_id="1", title_raw="Test Product",
    )
    PriceRecord.objects.create(
        store_product=store_product, price=Decimal("100"), currency="USD", price_date=today,
    )
    ProductDailyStat.objects.create(
        product=product, date=today,
        min_price=Decimal("100"), max_price=Decimal("100"), avg_price=Decimal("100"), currency="USD",
    )

    return product


class TestPriceDropSubscription:
    @pytest.fixture(autouse=True)
    def setup(self, product_with_today_stat):
        self.product = product_with_today_stat
        self.list_create_url = reverse("price-alert-list", args=[self.product.id])

    def test_create_requires_authentication(self, api_client):
        response = api_client.post(self.list_create_url, {
            "threshold_price": "90.00",
            "currency": "UAH",
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_subscription_success(self, auth_client, user):
        response = auth_client.post(self.list_create_url, {
            "threshold_price": "90.00",
            "currency": "UAH",
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert PriceDropSubscription.objects.filter(user=user, product=self.product).exists()

    def test_create_subscription_with_non_positive_price_fails(self, auth_client):
        response = auth_client.post(self.list_create_url, {
            "threshold_price": "0",
            "currency": "UAH",
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "threshold_price" in response.data

    def test_list_returns_only_own_subscriptions(self, auth_client, user, other_user):
        PriceDropSubscription.objects.create(
            user=user, product=self.product, threshold_price=Decimal("90"), currency="UAH",
        )
        PriceDropSubscription.objects.create(
            user=other_user, product=self.product, threshold_price=Decimal("80"), currency="UAH",
        )

        response = auth_client.get(self.list_create_url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert Decimal(response.data[0]["threshold_price"]) == Decimal("90")

    def test_delete_subscription(self, auth_client, user):
        subscription = PriceDropSubscription.objects.create(
            user=user, product=self.product, threshold_price=Decimal("90"), currency="UAH",
        )
        detail_url = reverse("price-alert-detail", args=[self.product.id, subscription.id])

        response = auth_client.delete(detail_url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not PriceDropSubscription.objects.filter(id=subscription.id).exists()

    def test_cannot_delete_other_users_subscription(self, auth_client, other_user):
        subscription = PriceDropSubscription.objects.create(
            user=other_user, product=self.product, threshold_price=Decimal("90"), currency="UAH",
        )
        detail_url = reverse("price-alert-detail", args=[self.product.id, subscription.id])

        response = auth_client.delete(detail_url)

        assert response.status_code == status.HTTP_404_NOT_FOUND