from django.urls import path

from alerts.api.views import PriceDropSubscriptionViewSet

price_alert_list = PriceDropSubscriptionViewSet.as_view({"get": "list", "post": "create"})
price_alert_detail = PriceDropSubscriptionViewSet.as_view({"delete": "destroy"})

urlpatterns = [
    path("products/<int:product_id>/price-alerts/", price_alert_list, name="price-alert-list"),
    path("products/<int:product_id>/price-alerts/<int:pk>/", price_alert_detail, name="price-alert-detail"),
]