from datetime import date as date_cls

import requests


class NbuExchangeRateClient:
    """Клієнт до публічного API Національного банку України"""

    URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange"
    TIMEOUT_SECONDS = 10

    def fetch_rates(self, target_date: date_cls) -> list[dict]:
        response = requests.get(
            self.URL,
            params={
                "date": target_date.strftime("%Y%m%d"),
                "json": "",
            },
            timeout=self.TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()  # [{"cc": "USD", "rate": 41.2, "exchangedate": "..."}, ...]
    