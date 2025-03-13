import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('CELERY_CONFIG_MODULE', 'core.celery_config')


celery = Celery('tinder')


celery.config_from_object('core.celery_config')


celery.autodiscover_tasks(['stack_partners'])


celery.conf.beat_schedule = {
    'generate-user-recommendations-nightly': {
        'task': 'stack_partners.tasks.generate_user_recommendations',
        'schedule': crontab(hour=3, minute=0),
        'options': {'queue': 'recommendations'},
    },
}

if __name__ == '__main__':
    celery.start() 