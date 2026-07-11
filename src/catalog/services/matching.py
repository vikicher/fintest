import re

from catalog.models import Product
from catalog.services.clients import RawProductData


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


class ProductMatchingService:
    """Проста евристика зіставлення одного й того ж товару між магазинами.
    Це явне спрощення для тестового завдання — реальні каталоги dummyjson і
    fakestoreapi між собою не перетинаються, у продакшн-сценарії тут був би
    окремий сервіс fuzzy-matching або ручна модерація."""

    @staticmethod
    def resolve_product(raw: RawProductData) -> Product:
        normalized = normalize_title(raw.title)
        product = Product.objects.filter(normalized_title=normalized).first()

        if product is None:
            product = Product.objects.create(
                title=raw.title,
                normalized_title=normalized,
                description=raw.description,
                image_url=raw.image_url,
            )

        return product