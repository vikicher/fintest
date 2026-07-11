from rest_framework import serializers

from alerts.models import PriceDropSubscription


class PriceDropSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceDropSubscription
        fields = ["id", "threshold_price", "currency", "is_active", "created_at", "triggered_at"]
        read_only_fields = ["id", "is_active", "created_at", "triggered_at"]

    def validate_threshold_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Ціна має бути більшою за нуль.")
        return value