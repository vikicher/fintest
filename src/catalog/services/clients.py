from dataclasses import dataclass
from decimal import Decimal

import requests

from catalog.models import Store


@dataclass
class RawProductData:
    external_id: str
    title: str
    description: str
    price: Decimal
    currency: str
    image_url: str = ""
    is_available: bool = True


class BaseStoreClient:
    store_code: str

    def fetch_products(self) -> list[RawProductData]:
        raise NotImplementedError


class DummyJsonClient(BaseStoreClient):
    store_code = Store.Code.DUMMYJSON
    URL = "https://dummyjson.com/products?limit=0"
    TIMEOUT_SECONDS = 10

    def fetch_products(self) -> list[RawProductData]:
        response = requests.get(self.URL, timeout=self.TIMEOUT_SECONDS)
        response.raise_for_status()
        items = response.json()["products"]

        return [
            RawProductData(
                external_id=str(item["id"]),
                title=item["title"],
                description=item.get("description", ""),
                price=Decimal(str(item["price"])),
                currency="USD",
                image_url=(item.get("images") or [""])[0],
                is_available=item.get("stock", 0) > 0,
            )
            for item in items
        ]


class FakeStoreApiClient(BaseStoreClient):
    store_code = Store.Code.FAKESTORE
    URL = "https://fakestoreapi.com/products"
    TIMEOUT_SECONDS = 10

    def fetch_products(self) -> list[RawProductData]:
        response = requests.get(self.URL, timeout=self.TIMEOUT_SECONDS)
        response.raise_for_status()
        items = response.json()

        return [
            RawProductData(
                external_id=str(item["id"]),
                title=item["title"],
                description=item.get("description", ""),
                price=Decimal(str(item["price"])),
                currency="USD",
                image_url=item.get("image", ""),
            )
            for item in items
        ]


STORE_CLIENTS: dict[str, type[BaseStoreClient]] = {
    Store.Code.DUMMYJSON: DummyJsonClient,
    Store.Code.FAKESTORE: FakeStoreApiClient,
}