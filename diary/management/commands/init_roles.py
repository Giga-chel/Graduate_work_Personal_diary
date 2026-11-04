from typing import Any

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Создаёт группы пользователей и назначает права'

    def handle(self, *args: Any, **options: Any) -> None:
        """Создаёт группы «Модераторы»/«Пользователи» с правами (идемпотентно)."""
        moderators, _ = Group.objects.get_or_create(name='Модераторы')

        change_perm = Permission.objects.get(
            codename='change_entry', content_type__app_label='diary'
        )
        view_perm = Permission.objects.get(
            codename='view_all_entries', content_type__app_label='diary'
        )

        moderators.permissions.add(change_perm, view_perm)

        Group.objects.get_or_create(name='Пользователи')
        self.stdout.write(self.style.SUCCESS('Группы и права готовы'))
