from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from alerts.models import PriceDropSubscription
from alerts.api.serializers import PriceDropSubscriptionSerializer


@extend_schema_view(
    list=extend_schema(
        summary="Список підписок на зниження ціни",
        description="Повертає власні підписки поточного користувача на вказаний товар.",
        parameters=[
            OpenApiParameter(
                name="product_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID товару",
            ),
        ],
    ),
    create=extend_schema(
        summary="Створити підписку на зниження ціни",
        description="Користувач отримає email, коли мінімальна ціна товару "
                     "опуститься нижче вказаного порогу.",
        parameters=[
            OpenApiParameter(
                name="product_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID товару",
            ),
        ],
    ),
    destroy=extend_schema(
        summary="Видалити підписку",
        parameters=[
            OpenApiParameter(
                name="product_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID товару",
            ),
        ],
    ),
)
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