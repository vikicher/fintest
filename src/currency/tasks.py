from celery import shared_task
from django.utils import timezone

from currency.services import ExchangeRateSyncService


@shared_task
def sync_today_rates() -> None:
    ExchangeRateSyncService().sync_for_date(timezone.localdate())
