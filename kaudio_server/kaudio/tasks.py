from celery import shared_task
from django.core.mail import send_mail

@shared_task
def print_hello():
    print("Hello from Celery!")
    return "Hello from Celery!"

@shared_task
def send_statistics_email():
    send_mail(
        'Статистика',
        'Ваш отчёт готов!',
        'from@example.com',
        ['to@example.com'],
        fail_silently=False,
    ) 
    
# celery -A kaudio_server.celery_app:celery worker -l info --pool=solo
# celery -A kaudio_server.celery_app:celery beat -l info