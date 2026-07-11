from django.urls import path

from catalog.api.views import (
    ProductListView,
    ProductDetailView,
    ProductOffersView,
    ProductPriceHistoryView,
)

urlpatterns = [
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path("products/<int:pk>/offers/", ProductOffersView.as_view(), name="product-offers"),
    path("products/<int:pk>/price-history/", ProductPriceHistoryView.as_view(), name="product-price-history"),
]