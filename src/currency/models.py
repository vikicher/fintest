from django.db import models


class ExchangeRate(models.Model):
    currency_code = models.CharField(max_length=3)  # USD, EUR ...
    rate_to_uah = models.DecimalField(max_digits=12, decimal_places=6)
    rate_date = models.DateField()

    class Meta:
        unique_together = ("currency_code", "rate_date")
        indexes = [models.Index(fields=["currency_code", "-rate_date"])]

    def __str__(self) -> str:
        return f"{self.currency_code} -> UAH ({self.rate_date}): {self.rate_to_uah}"