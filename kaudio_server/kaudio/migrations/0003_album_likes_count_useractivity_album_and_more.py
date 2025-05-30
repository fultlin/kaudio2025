# Generated by Django 5.0.6 on 2025-05-11 10:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kaudio', '0002_track_audio_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='album',
            name='likes_count',
            field=models.PositiveIntegerField(default=0, verbose_name='Количество лайков'),
        ),
        migrations.AddField(
            model_name='useractivity',
            name='album',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_activities', to='kaudio.album', verbose_name='Альбом'),
        ),
        migrations.AlterField(
            model_name='useractivity',
            name='activity_type',
            field=models.CharField(choices=[('play', 'Воспроизведение'), ('like', 'Лайк'), ('like_album', 'Лайк альбома'), ('add_to_playlist', 'Добавление в плейлист'), ('follow_artist', 'Подписка на исполнителя')], max_length=20, verbose_name='Тип активности'),
        ),
    ]
