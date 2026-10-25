from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Создаёт группы пользователей и назначает права'

    def handle(self, *args, **options):
        moderators, _ = Group.objects.get_or_create(name='Модераторы')
        moderators.permissions.add(
            Permission.objects.get(codename='view_all_entries'),
        )
        Group.objects.get_or_create(name='Пользователи')
        self.stdout.write(self.style.SUCCESS('Группы и права готовы'))
