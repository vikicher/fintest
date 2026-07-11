from rest_framework import serializers

from catalog.choices import Trend


class ProductListItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    price_from = serializers.DecimalField(max_digits=12, decimal_places=2)
    price_to = serializers.DecimalField(max_digits=12, decimal_places=2)
    trend = serializers.ChoiceField(choices=Trend.choices)
    currency = serializers.CharField()


class ProductDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()
    price_from = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    price_to = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    currency = serializers.CharField()


class StoreOfferSerializer(serializers.Serializer):
    store = serializers.CharField()
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()


class PriceHistoryPointSerializer(serializers.Serializer):
    date = serializers.DateField()
    average = serializers.DecimalField(max_digits=12, decimal_places=2)
    by_store = serializers.DictField(child=serializers.DecimalField(max_digits=12, decimal_places=2))
