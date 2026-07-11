from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from alerts.models import PriceDropSubscription
from alerts.api.serializers import PriceDropSubscriptionSerializer


class PriceDropSubscriptionViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    serializer_class = PriceDropSubscriptionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return PriceDropSubscription.objects.filter(
            user=self.request.user,
            product_id=self.kwargs["product_id"],
        )

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            product_id=self.kwargs["product_id"],
        )