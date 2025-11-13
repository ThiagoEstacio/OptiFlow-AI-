"""
Celery application configuration
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "optiflow",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'app.tasks.data_tasks',  # Data collection tasks
        'app.tasks.ml_tasks',    # ML training tasks
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Celery Beat Schedule - Periodic Tasks
celery_app.conf.beat_schedule = {
    # Retreinar modelos ML toda segunda-feira às 2am
    'retrain-ml-models-weekly': {
        'task': 'ml.retrain_models',
        'schedule': crontab(hour=2, minute=0, day_of_week=1),  # Segunda 2am
        'kwargs': {'models_to_train': 'all'}
    },

    # Validar modelos ML todos os dias às 3am
    'validate-ml-models-daily': {
        'task': 'ml.validate_models',
        'schedule': crontab(hour=3, minute=0),  # Diariamente 3am
    },

    # Limpar modelos antigos (>30 dias) primeiro dia do mês às 4am
    'cleanup-old-models-monthly': {
        'task': 'ml.cleanup_old_models',
        'schedule': crontab(hour=4, minute=0, day_of_month=1),  # 1º dia do mês 4am
        'kwargs': {'days_to_keep': 30}
    },
}

