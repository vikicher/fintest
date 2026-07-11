from celery import shared_task
from django.core.mail import send_mail

from alerts.models import PriceDropSubscription


@shared_task
def send_price_drop_email(subscription_id: int, current_price: str) -> None:
    subscription = (
        PriceDropSubscription.objects
        .select_related("user", "product")
        .get(id=subscription_id)
    )

    send_mail(
        subject=f"Ціна на «{subscription.product.title}» знизилась",
        message=(
            f"Поточна мінімальна ціна: {current_price} {subscription.currency}\n"
            f"Ваш поріг: {subscription.threshold_price} {subscription.currency}"
        ),
        from_email=None,
        recipient_list=[subscription.user.email],
    )