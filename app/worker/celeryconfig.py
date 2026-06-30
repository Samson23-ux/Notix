from celery.schedules import crontab

task_acks_late = True
worker_concurrency = 100
timezone = "Africa/Lagos"
reject_on_worker_lost = True
worker_prefetch_multiplier = 1

task_routes = {
    "app.worker.tasks.email.send_email_task": {"queue": "notix.standard"},
    "app.worker.tasks.email.send_verification_email": {"queue": "notix.standard"},
    "app.worker.tasks.email.send_critical_email_task": {"queue": "notix.high"},
    "app.worker.tasks.webhook.deliver_webhook_task": {"queue": "notix.webhook"},
    "app.worker.tasks.digest.collect_and_send_digests": {"queue": "notix.batch"},
    "app.worker.tasks.dlq.monitor_dlq": {"queue": "notix.dlq"},
}


beat_schedule = {
    "digest": {
        "task": "app.worker.tasks.digest.collect_and_send_digests",
        "schedule": crontab(hour="*/1"),
    },
    "dlq": {
        "task": "app.worker.tasks.dlq.monitor_dlq",
        "schedule": crontab(minute="*/5"),
    },
}
