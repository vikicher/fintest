from django.utils import timezone

from catalog.models import Store, StoreProduct, PriceRecord
from catalog.services.clients import STORE_CLIENTS, BaseStoreClient
from catalog.services.matching import ProductMatchingService


class ProductSyncService:
    """Синхронізує товари й ціни одного магазину з його зовнішнім API"""

    def __init__(self, store: Store, client: BaseStoreClient | None = None):
        self.store = store
        self.client = client or STORE_CLIENTS[store.code]()

    def sync(self) -> None:
        today = timezone.localdate()

        for raw in self.client.fetch_products():
            product = ProductMatchingService.resolve_product(raw)

            store_product, _ = StoreProduct.objects.update_or_create(
                store=self.store,
                external_id=raw.external_id,
                defaults={
                    "product": product,
                    "title_raw": raw.title,
                    "is_available": raw.is_available,
                    "last_synced_at": timezone.now(),
                },
            )

            PriceRecord.objects.update_or_create(
                store_product=store_product,
                price_date=today,
                defaults={
                    "price": raw.price,
                    "currency": raw.currency,
                },
            )
