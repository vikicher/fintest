import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from catalog.models import Store, Product, StoreProduct, PriceRecord, ProductDailyStat
from currency.models import ExchangeRate
from users.models import User


class Command(BaseCommand):
    help = "Наповнює базу демо-даними: суперкористувач, магазини, товари, історія цін, курс валют"

    def handle(self, *args, **options):
        today = timezone.localdate()

        self.stdout.write("Створюю суперкористувача...")
        superuser, created = User.objects.get_or_create(
            email="admin@admin.com",
            defaults={"is_staff": True, "is_superuser": True},
        )
        superuser.set_password("admin")
        superuser.is_staff = True
        superuser.is_superuser = True
        superuser.save()
        self.stdout.write(self.style.SUCCESS(
            f"Суперкористувач: admin@admin.com / admin ({'створено' if created else 'оновлено'})"
        ))

        self.stdout.write("Створюю звичайного тестового користувача...")
        test_user, _ = User.objects.get_or_create(email="user@example.com")
        test_user.set_password("user12345")
        test_user.save()
        self.stdout.write(self.style.SUCCESS("Тестовий користувач: user@example.com / user12345"))

        self.stdout.write("Створюю курс валют НБУ (USD→UAH)...")
        for days_ago in range(0, 35):
            rate_date = today - timezone.timedelta(days=days_ago)
            # невеликі коливання курсу для реалістичності
            rate_value = Decimal("41.00") + Decimal(str(round(random.uniform(-0.5, 0.5), 2)))
            ExchangeRate.objects.update_or_create(
                currency_code="USD", rate_date=rate_date,
                defaults={"rate_to_uah": rate_value},
            )
        self.stdout.write(self.style.SUCCESS("Курси валют створено за останні 35 днів"))

        self.stdout.write("Створюю магазини...")
        store_dummyjson, _ = Store.objects.get_or_create(
            code=Store.Code.DUMMYJSON, defaults={"name": "DummyJSON", "base_currency": "USD"},
        )
        store_fakestore, _ = Store.objects.get_or_create(
            code=Store.Code.FAKESTORE, defaults={"name": "FakeStoreAPI", "base_currency": "USD"},
        )
        self.stdout.write(self.style.SUCCESS("Магазини створено"))

        self.stdout.write("Створюю товари з історією цін...")

        # (назва, опис, базова ціна, тренд: up/down/same)
        demo_products = [
            ("iPhone 15 Pro", "Флагманський смартфон Apple з чіпом A17 Pro", Decimal("999"), "up"),
            ("Samsung Galaxy S24", "Топовий Android-смартфон з AI-функціями", Decimal("899"), "down"),
            ("MacBook Air M3", "Ультратонкий ноутбук Apple на чіпі M3", Decimal("1299"), "same"),
            ("Sony WH-1000XM5", "Навушники з активним шумозаглушенням", Decimal("349"), "down"),
            ("Nintendo Switch OLED", "Портативна ігрова консоль з OLED-екраном", Decimal("349"), "up"),
            ("Dyson V15", "Бездротовий пилосос з лазерним детектором пилу", Decimal("749"), "same"),
            ("Kindle Paperwhite", "Електронна книга з підсвіткою", Decimal("139"), "down"),
            ("GoPro Hero 12", "Екшн-камера для активного відпочинку", Decimal("399"), "up"),
        ]

        for title, description, base_price, trend in demo_products:
            product, _ = Product.objects.get_or_create(
                normalized_title=title.lower(),
                defaults={"title": title, "description": description},
            )
            product.description = description
            product.save(update_fields=["description"])

            store_product_a, _ = StoreProduct.objects.get_or_create(
                store=store_dummyjson, product=product,
                defaults={"external_id": f"dj-{product.id}", "title_raw": title},
            )
            store_product_b, _ = StoreProduct.objects.get_or_create(
                store=store_fakestore, product=product,
                defaults={"external_id": f"fs-{product.id}", "title_raw": title},
            )

            self._create_price_history(store_product_a, store_product_b, base_price, trend, today)
            self._recalculate_daily_stats(product, today)

        self.stdout.write(self.style.SUCCESS(f"Створено {len(demo_products)} товарів з історією цін"))
        self.stdout.write(self.style.SUCCESS("Готово! Можна логінитись і перевіряти API."))

    def _create_price_history(self, store_product_a, store_product_b, base_price, trend, today):
        """Генерує ціни за останні 30 днів з заданим трендом.
        'up' — ціна сьогодні вища за 30 днів тому, 'down' — нижча, 'same' — приблизно та сама."""

        for days_ago in range(30, -1, -1):
            price_date = today - timezone.timedelta(days=days_ago)
            progress = (30 - days_ago) / 30  # від 0.0 (30 днів тому) до 1.0 (сьогодні)

            if trend == "up":
                trend_multiplier = Decimal("1") + Decimal("0.15") * Decimal(str(progress))
            elif trend == "down":
                trend_multiplier = Decimal("1") - Decimal("0.15") * Decimal(str(progress))
            else:
                trend_multiplier = Decimal("1")

            noise_a = Decimal(str(round(random.uniform(-0.02, 0.02), 4)))
            noise_b = Decimal(str(round(random.uniform(-0.02, 0.02), 4)))

            price_a = (base_price * trend_multiplier * (Decimal("1") + noise_a)).quantize(Decimal("0.01"))
            price_b = (base_price * trend_multiplier * (Decimal("1") + noise_b) * Decimal("1.05")).quantize(Decimal("0.01"))

            PriceRecord.objects.update_or_create(
                store_product=store_product_a, price_date=price_date,
                defaults={"price": price_a, "currency": "USD"},
            )
            PriceRecord.objects.update_or_create(
                store_product=store_product_b, price_date=price_date,
                defaults={"price": price_b, "currency": "USD"},
            )

    def _recalculate_daily_stats(self, product, today):
        """Перераховує ProductDailyStat за всі дні, де є PriceRecord для цього товару"""
        from django.db.models import Min, Max, Avg

        dates = (
            PriceRecord.objects
            .filter(store_product__product=product)
            .values_list("price_date", flat=True)
            .distinct()
        )

        for price_date in dates:
            aggregate = (
                PriceRecord.objects
                .filter(store_product__product=product, price_date=price_date)
                .aggregate(min_p=Min("price"), max_p=Max("price"), avg_p=Avg("price"))
            )
            ProductDailyStat.objects.update_or_create(
                product=product, date=price_date,
                defaults={
                    "min_price": aggregate["min_p"],
                    "max_price": aggregate["max_p"],
                    "avg_price": aggregate["avg_p"],
                    "currency": "USD",
                },
            )