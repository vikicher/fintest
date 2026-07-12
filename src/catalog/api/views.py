from datetime import timedelta
from collections import defaultdict

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter

from catalog.choices import Trend
from catalog.models import Product, ProductDailyStat, PriceRecord
from catalog.api.serializers import (
    ProductListItemSerializer,
    ProductDetailSerializer,
    StoreOfferSerializer,
    PriceHistoryPointSerializer,
)
from catalog.services.trend import TrendService
from currency.services import CurrencyConversionService


class CurrencyParamMixin:
    DEFAULT_CURRENCY = "UAH"

    def get_currency(self) -> str:
        return self.request.query_params.get("currency", self.DEFAULT_CURRENCY).upper()


class ProductListView(CurrencyParamMixin, ListAPIView):
    serializer_class = ProductListItemSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Список товарів",
        description="Назва, діапазон цін на сьогодні, тренд ціни порівняно "
                    "із середньою за попередні 30 днів.",
        parameters=[
            OpenApiParameter(name="currency", type=str, description="Код валюти, напр. UAH, USD"),
            OpenApiParameter(name="sort", type=str, description="price або trend"),
            OpenApiParameter(name="order", type=str, description="asc або desc"),
        ],
    )
    def get(self, request, *args, **kwargs):
        currency = self.get_currency()
        today = timezone.localdate()
        sort = request.query_params.get("sort", "price")   # price | trend
        order = request.query_params.get("order", "asc")

        queryset = ProductDailyStat.objects.filter(date=today).select_related("product")
        if sort == "price":
            ordering_field = "avg_price" if order == "asc" else "-avg_price"
            queryset = queryset.order_by(ordering_field)

        page = self.paginate_queryset(queryset)

        items = []
        for stat in page:
            trend, _ = TrendService.calculate(stat.product_id, today)
            items.append({
                "id": stat.product_id,
                "title": stat.product.title,
                "price_from": CurrencyConversionService.convert(stat.min_price, "USD", currency),
                "price_to": CurrencyConversionService.convert(stat.max_price, "USD", currency),
                "trend": trend,
                "currency": currency,
            })

        if sort == "trend":
            trend_order = {Trend.DOWN: 0, Trend.SAME: 1, Trend.UP: 2}
            items.sort(key=lambda item: trend_order[item["trend"]], reverse=(order == "desc"))

        serializer = ProductListItemSerializer(items, many=True)
        return self.get_paginated_response(serializer.data)


class ProductDetailView(CurrencyParamMixin, RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductDetailSerializer

    @extend_schema(
        summary="Картка товару",
        description="Назва, опис товару, діапазон цін (від/до) на сьогодні у вказаній валюті.",
        parameters=[
            OpenApiParameter(
                name="currency",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Код валюти, напр. UAH, USD. За замовчуванням — UAH.",
            ),
        ],
        responses=ProductDetailSerializer,
    )
    def get(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Product, pk=pk)
        currency = self.get_currency()
        today = timezone.localdate()
        stat = ProductDailyStat.objects.filter(product=product, date=today).first()

        data = {
            "id": product.id,
            "title": product.title,
            "description": product.description,
            "price_from": CurrencyConversionService.convert(stat.min_price, "USD", currency) if stat else None,
            "price_to": CurrencyConversionService.convert(stat.max_price, "USD", currency) if stat else None,
            "currency": currency,
        }
        serializer = ProductDetailSerializer(data)
        return Response(serializer.data)


class ProductOffersView(CurrencyParamMixin, APIView):
    """"Показати всі ціни" — список пар магазин/ціна на сьогодні"""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Всі ціни на товар",
        description="Список пар магазин/ціна на сьогодні у вказаній валюті.",
        parameters=[
            OpenApiParameter(
                name="currency",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Код валюти, напр. UAH, USD. За замовчуванням — UAH.",
            ),
        ],
        responses=StoreOfferSerializer(many=True),
    )
    def get(self, request, pk, *args, **kwargs):
        currency = self.get_currency()
        today = timezone.localdate()

        records = (
            PriceRecord.objects
            .filter(store_product__product_id=pk, price_date=today)
            .select_related("store_product__store")
        )

        data = [
            {
                "store": record.store_product.store.name,
                "price": CurrencyConversionService.convert(record.price, record.currency, currency),
                "currency": currency,
            }
            for record in records
        ]
        serializer = StoreOfferSerializer(data, many=True)
        return Response(serializer.data)


class ProductPriceHistoryView(CurrencyParamMixin, APIView):
    """"Показати історію цін" — дані для графіка по магазинах і середньої ціни"""

    permission_classes = [AllowAny]
    DEFAULT_DAYS = 30

    @extend_schema(
        summary="Історія цін товару",
        description="Дані для графіка: динаміка цін по магазинах та середньої ціни, згруповані по днях.",
        parameters=[
            OpenApiParameter(
                name="currency",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Код валюти, напр. UAH, USD. За замовчуванням — UAH.",
            ),
            OpenApiParameter(
                name="days",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Кількість днів історії. За замовчуванням — 30.",
            ),
        ],
        responses=PriceHistoryPointSerializer(many=True),
    )
    def get(self, request, pk, *args, **kwargs):
        currency = self.get_currency()
        days = int(request.query_params.get("days", self.DEFAULT_DAYS))
        date_from = timezone.localdate() - timedelta(days=days)

        records = (
            PriceRecord.objects
            .filter(store_product__product_id=pk, price_date__gte=date_from)
            .select_related("store_product__store")
        )

        prices_by_date: dict = defaultdict(dict)
        for record in records:
            converted_price = CurrencyConversionService.convert(
                record.price, record.currency, currency, record.price_date,
            )
            prices_by_date[record.price_date][record.store_product.store.name] = converted_price

        points = []
        for point_date, store_prices in sorted(prices_by_date.items()):
            average_price = sum(store_prices.values()) / len(store_prices)
            points.append({
                "date": point_date,
                "average": average_price,
                "by_store": store_prices,
            })

        serializer = PriceHistoryPointSerializer(points, many=True)
        return Response(serializer.data)