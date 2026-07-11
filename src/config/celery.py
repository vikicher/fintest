from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "sync-stores-and-check-alerts": {
        "task": "catalog.tasks.sync_all_stores",
        "schedule": crontab(hour=3, minute=0),
    },
    "sync-exchange-rates": {
        "task": "currency.tasks.sync_today_rates",
        "schedule": crontab(hour=2, minute=30),
    },
}
