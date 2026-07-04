from kombu import Queue
from celery.schedules import crontab

task_acks_late = True
worker_concurrency = 100
timezone = "Africa/Lagos"
reject_on_worker_lost = True
worker_prefetch_multiplier = 1

queue_args = {
    "x-max-priority": 10,
    "x-dead-letter-routing-key": "dlq",
    "x-dead-letter-exchange": "notix.dlx",
}

task_queues = (
    Queue("notix.dlq", "notix.dlx", "dlq"),
    Queue("notix.high", "notix.direct", "high", queue_arguments=queue_args),
    Queue("notix.batch", "notix.direct", "batch", queue_arguments=queue_args),
    Queue("notix.webhook", "notix.direct", "webhook", queue_arguments=queue_args),
    Queue("notix.standard", "notix.direct", "standard", queue_arguments=queue_args),
)

task_routes = {
    "app.worker.tasks.email.send_email_task": {"queue": "notix.standard"},
    "app.worker.tasks.email.send_verification_email": {"queue": "notix.standard"},
    "app.worker.tasks.email.send_critical_email_task": {"queue": "notix.high"},
    "app.worker.tasks.webhook.deliver_webhook_task": {"queue": "notix.webhook"},
    "app.worker.tasks.digest.collect_and_send_digests": {"queue": "notix.batch"},
    "app.worker.tasks.dlq.monitor_dlq": {"queue": "notix.standard"},
}


beat_schedule = {
    "digest": {
        "task": "app.worker.tasks.digest.collect_and_send_digests",
        "schedule": crontab(minute="0", hour="*"),
    },
    "dlq": {
        "task": "app.worker.tasks.dlq.monitor_dlq",
        "schedule": crontab(minute="*/5"),
    },
}
