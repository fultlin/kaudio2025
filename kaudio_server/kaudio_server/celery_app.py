from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kaudio_server.settings')

celery = Celery('kaudio_server')
celery.config_from_object('django.conf:settings', namespace='CELERY')
celery.autodiscover_tasks() 