# Generated by Django 5.0.6 on 2025-06-14 14:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kaudio', '0007_artist_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='artist',
            name='username',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Имя пользователя'),
        ),
    ]
