from django.conf import settings
from django.db import models


class Entry(models.Model):
    """Запись в личном дневнике."""

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

    def __str__(self):
        return self.title
