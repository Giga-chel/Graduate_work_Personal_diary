from django.conf import settings
from django.db import models


class Entry(models.Model):
    """Запись личного дневника: заголовок, текст, автор, время создания."""

    title = models.CharField('заголовок', max_length=200)
    content = models.TextField('содержание')
    created_at = models.DateTimeField('дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('дата обновления', auto_now=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='entries',
        verbose_name='автор',
    )

    class Meta:
        verbose_name = 'запись'
        verbose_name_plural = 'записи'
        ordering = ['-created_at']
        permissions = [('view_all_entries', 'Может просматривать чужие записи')]

    def __str__(self) -> str:
        """Возвращает заголовок записи (для админки и списков)."""
        return self.title
