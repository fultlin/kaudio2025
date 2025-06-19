from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
from django.utils.translation import gettext as _
from django.db.models import F, ExpressionWrapper, FloatField
from django.http import HttpResponse
from typing import List, Any, Union
import os

# Регистрируем шрифт Montserrat вместо DejaVuSans
font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                        'kaudio_client', 'src', 'fonts', 'Montserrat-Medium.ttf')
pdfmetrics.registerFont(TTFont('Montserrat', font_path))

def calculate_popularity_score(track: 'Track') -> float:
    """
    Вычисляет рейтинг популярности трека.
    
    Использует взвешенную формулу, учитывающую количество прослушиваний и лайков.
    
    Args:
        track: Объект трека для расчета популярности
        
    Returns:
        float: Рейтинг популярности от 0 до 100
    """
    play_weight = 0.6
    like_weight = 0.4
    max_plays = 1000  # Нормализующее значение для прослушиваний
    max_likes = 100   # Нормализующее значение для лайков
    
    normalized_plays = min(track.play_count / max_plays, 1.0)
    normalized_likes = min(track.likes_count / max_likes, 1.0)
    
    return (normalized_plays * play_weight + normalized_likes * like_weight) * 100

def generate_track_pdf(tracks: List['Track'], response: HttpResponse) -> None:
    """
    Генерирует PDF документ со списком треков.
    
    Создает таблицу с информацией о треках включая название, исполнителя,
    альбом, длительность, статистику и рейтинг популярности.
    
    Args:
        tracks: Список треков для включения в отчет
        response: HTTP ответ для записи PDF
    """
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    
    # Стили
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName='Montserrat',  # Используем Montserrat
        fontSize=16,
        spaceAfter=30
    )
    
    # Заголовок
    elements.append(Paragraph(_("Отчет по трекам"), title_style))
    elements.append(Spacer(1, 12))
    
    # Данные для таблицы
    data = [[
        _("Название"),
        _("Исполнитель"),
        _("Альбом"),
        _("Длительность"),
        _("Прослушивания"),
        _("Лайки"),
        _("Рейтинг")
    ]]
    
    for track in tracks:
        data.append([
            track.title,
            track.artist.email if track.artist else _("Нет исполнителя"),
            track.album.title if track.album else _("Нет альбома"),
            f"{track.duration // 60}:{track.duration % 60:02d}",
            str(track.play_count),
            str(track.likes_count),
            f"{calculate_popularity_score(track):.2f}"
        ])
    
    # Создаем таблицу
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Montserrat'),  # Используем Montserrat
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    
    elements.append(table)
    doc.build(elements)

def generate_album_pdf(albums: List['Album'], response: HttpResponse) -> None:
    """
    Генерирует PDF документ со списком альбомов.
    
    Создает таблицу с информацией об альбомах включая название, исполнителя,
    дату выпуска, количество треков, длительность и жанры.
    
    Args:
        albums: Список альбомов для включения в отчет
        response: HTTP ответ для записи PDF
    """
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    
    # Стили
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName='Montserrat',  # Используем Montserrat
        fontSize=16,
        spaceAfter=30
    )
    
    # Заголовок
    elements.append(Paragraph(_("Отчет по альбомам"), title_style))
    elements.append(Spacer(1, 12))
    
    # Данные для таблицы
    data = [[
        _("Название"),
        _("Исполнитель"),
        _("Дата выпуска"),
        _("Треков"),
        _("Длительность"),
        _("Жанры")
    ]]
    
    for album in albums:
        genres = ", ".join([genre.title for genre in album.genres.all()])
        data.append([
            album.title,
            album.artist.email if album.artist else _("Нет исполнителя"),
            album.release_date.strftime("%d.%m.%Y"),
            str(album.total_tracks),
            f"{album.total_duration // 60}:{album.total_duration % 60:02d}",
            genres or _("Нет жанров")
        ])
    
    # Создаем таблицу
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Montserrat'),  # Используем Montserrat
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    
    elements.append(table)
    doc.build(elements)
