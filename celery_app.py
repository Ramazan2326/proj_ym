from celery import Celery
from celery.schedules import crontab

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()  # Автопоиск задач

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    task_max_retries=5,
)

app.conf.beat_schedule = {
    "check_missing_whooks": {
        "task": "whooks.tasks.check_missing_whooks",
        "schedule": crontab(minute="*/5"),
    },
}
