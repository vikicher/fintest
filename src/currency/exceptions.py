class CurrencyRateUnavailable(Exception):
    """Курс валюти на потрібну дату (або раніше) відсутній у базі"""

    def __init__(self, currency_code: str):
        self.currency_code = currency_code
        super().__init__(f"Немає курсу для валюти {currency_code}")
        