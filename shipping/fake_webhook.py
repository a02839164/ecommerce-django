from shipping.tasks import send_fake_webhook_task


def simulate_fake_webhook(tracking_number):
    """
    逐段模擬物流狀態：
    PRE_TRANSIT → IN_TRANSIT → OUT_FOR_DELIVERY → DELIVERED
    """

    STAGES = [
        ("PRE_TRANSIT", 60),
        ("IN_TRANSIT", 120),
        ("OUT_FOR_DELIVERY", 180),
        ("DELIVERED", 240),
    ]

    for status, delay in STAGES:
        send_fake_webhook_task.apply_async(
            args=[tracking_number, status],
            countdown=delay
        )

    return True