from celery import shared_task
from django.utils import timezone

from catalog.models import Store
from catalog.services.sync import ProductSyncService
from catalog.services.stats import StatsCalculationService
from alerts.services import PriceAlertService


@shared_task
def sync_all_stores() -> None:
    for store in Store.objects.filter(is_active=True):
        ProductSyncService(store).sync()

    today = timezone.localdate()
    StatsCalculationService.calculate_for_date(today)
    PriceAlertService.check_and_notify(today)