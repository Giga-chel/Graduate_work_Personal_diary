from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from diary.models import Entry

User = get_user_model()

URL_LIST = 'diary:entry_list'
URL_DETAIL = 'diary:entry_detail'
URL_CREATE = 'diary:entry_create'
URL_UPDATE = 'diary:entry_update'
URL_DELETE = 'diary:entry_delete'
URL_REGISTER = 'diary:register'


class BaseDiaryTestCase(TestCase):
    """Общая подготовка: пользователи, группа модераторов, помощники."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.author = User.objects.create_user(
            username='ivan', password='Ivan12345'
        )
        cls.stranger = User.objects.create_user(
            username='marina', password='Marina12345'
        )
        cls.moderator = User.objects.create_user(
            username='moderator', password='Moder12345'
        )
        moderators = Group.objects.get_or_create(name='Модераторы')[0]
        perms = Permission.objects.filter(
            content_type__app_label='diary',
            codename__in=['view_all_entries', 'change_entry'],
        )
        moderators.permissions.set(perms)
        cls.moderator.groups.add(moderators)

    def make_entry(
        self, owner: User, title: str = 'Запись', content: str = 'Текст'
    ) -> Entry:
        return Entry.objects.create(
            owner=owner, title=title, content=content
        )


class AuthTests(BaseDiaryTestCase):
    """Регистрация, вход, редиректы для анонима."""

    def test_register_page_available(self) -> None:
        response = self.client.get(reverse(URL_REGISTER))
        self.assertEqual(response.status_code, 200)

    def test_register_creates_user_and_logs_in(self) -> None:
        """Успешная регистрация создаёт пользователя и сразу авторизует."""
        response = self.client.post(reverse(URL_REGISTER), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'SuperPass123',
            'password2': 'SuperPass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertTrue(self.client.session.get('_auth_user_id'))

    def test_register_rejects_password_mismatch(self) -> None:
        self.client.post(reverse(URL_REGISTER), {
            'username': 'newuser',
            'email': 'other@example.com',
            'password1': 'SuperPass123',
            'password2': 'Other12345',
        })
        self.assertFalse(
            User.objects.filter(username='newuser').exists()
        )

    def test_register_rejects_duplicate_username(self) -> None:
        response = self.client.post(reverse(URL_REGISTER), {
            'username': 'ivan',
            'email': 'other@example.com',
            'password1': 'SuperPass123',
            'password2': 'SuperPass123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)

    def test_login_existing_user(self) -> None:
        response = self.client.post(
            reverse('login'),
            {'username': 'ivan', 'password': 'Ivan12345'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.client.get(reverse(URL_LIST)).status_code, 200
        )

    def test_anonymous_redirects_to_login_from_list(self) -> None:
        response = self.client.get(reverse(URL_LIST))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login', response['Location'])

    def test_anonymous_redirects_to_login_from_create(self) -> None:
        response = self.client.get(reverse(URL_CREATE))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login', response['Location'])


class EntryCrudTests(BaseDiaryTestCase):
    """CRUD своих записей."""

    def setUp(self) -> None:
        self.client.force_login(self.author)

    def test_create_entry(self) -> None:
        response = self.client.post(reverse(URL_CREATE), {
            'title': 'Новая запись', 'content': 'Содержимое',
        })
        self.assertEqual(response.status_code, 302)
        entry = Entry.objects.get(title='Новая запись')
        self.assertEqual(entry.owner, self.author)

    def test_list_shows_only_own_entries(self) -> None:
        self.make_entry(self.author, title='Моя запись')
        self.make_entry(self.stranger, title='Чужая запись')
        response = self.client.get(reverse(URL_LIST))
        self.assertContains(response, 'Моя запись')
        self.assertNotContains(response, 'Чужая запись')

    def test_detail_own_entry(self) -> None:
        entry = self.make_entry(
            self.author, content='Особенный текст'
        )
        response = self.client.get(
            reverse(URL_DETAIL, args=[entry.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Особенный текст')

    def test_update_own_entry(self) -> None:
        entry = self.make_entry(self.author)
        response = self.client.post(
            reverse(URL_UPDATE, args=[entry.pk]),
            {'title': 'Обновлённый', 'content': 'Новый текст'},
        )
        self.assertEqual(response.status_code, 302)
        entry.refresh_from_db()
        self.assertEqual(entry.title, 'Обновлённый')

    def test_delete_own_entry(self) -> None:
        entry = self.make_entry(self.author)
        response = self.client.post(
            reverse(URL_DELETE, args=[entry.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Entry.objects.filter(pk=entry.pk).exists()
        )

    def test_entry_str_returns_title(self) -> None:
        entry = self.make_entry(self.author, title='Проверка строки')
        self.assertEqual(str(entry), 'Проверка строки')


class IsolationTests(BaseDiaryTestCase):
    """Чужие записи недоступны обычному пользователю."""

    def setUp(self) -> None:
        self.entry = self.make_entry(self.author)
        self.client.force_login(self.stranger)

    def test_cannot_view_foreign_entry(self) -> None:
        response = self.client.get(
            reverse(URL_DETAIL, args=[self.entry.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_cannot_update_foreign_entry(self) -> None:
        response = self.client.post(
            reverse(URL_UPDATE, args=[self.entry.pk]),
            {'title': 'Взломано', 'content': 'хак'},
        )
        self.assertEqual(response.status_code, 404)
        self.entry.refresh_from_db()
        self.assertNotEqual(self.entry.title, 'Взломано')

    def test_cannot_delete_foreign_entry(self) -> None:
        response = self.client.post(
            reverse(URL_DELETE, args=[self.entry.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            Entry.objects.filter(pk=self.entry.pk).exists()
        )


class ModeratorTests(BaseDiaryTestCase):
    """Модератор видит и правит любые записи."""

    def setUp(self) -> None:
        self.entry = self.make_entry(
            self.author, title='Запись Ивана'
        )
        self.client.force_login(self.moderator)

    def test_moderator_sees_all_entries(self) -> None:
        self.make_entry(self.stranger, title='Запись Марины')
        response = self.client.get(reverse(URL_LIST))
        self.assertContains(response, 'Запись Ивана')
        self.assertContains(response, 'Запись Марины')

    def test_moderator_updates_foreign_entry(self) -> None:
        response = self.client.post(
            reverse(URL_UPDATE, args=[self.entry.pk]),
            {'title': 'Поправлено', 'content': 'ok'},
        )
        self.assertEqual(response.status_code, 302)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.title, 'Поправлено')

    def test_moderator_deletes_foreign_entry(self) -> None:
        response = self.client.post(
            reverse(URL_DELETE, args=[self.entry.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Entry.objects.filter(pk=self.entry.pk).exists()
        )


class SearchTests(BaseDiaryTestCase):
    """Поиск по заголовку и содержимому."""

    def setUp(self) -> None:
        self.client.force_login(self.author)
        self.make_entry(
            self.author, title='Отчёт за июнь', content='Квартал закрыт'
        )
        self.make_entry(
            self.author, title='Мысли', content='Июнь выдался жарким'
        )

    def test_search_by_title(self) -> None:
        response = self.client.get(
            reverse(URL_LIST), {'q': 'отчёт'}
        )
        self.assertContains(response, 'Отчёт за июнь')
        self.assertNotContains(response, 'Мысли')

    def test_search_by_content(self) -> None:
        response = self.client.get(
            reverse(URL_LIST), {'q': 'жарким'}
        )
        self.assertContains(response, 'Мысли')
        self.assertNotContains(response, 'Отчёт за июнь')

    def test_search_without_results(self) -> None:
        response = self.client.get(
            reverse(URL_LIST), {'q': 'qqqqq'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['entries']), 0)


class PaginationTests(BaseDiaryTestCase):
    """Пагинация (paginate_by = 6)."""

    def setUp(self) -> None:
        self.client.force_login(self.author)
        for i in range(1, 8):
            self.make_entry(self.author, title=f'Запись №{i}')

    def test_first_page_is_limited(self) -> None:
        response = self.client.get(reverse(URL_LIST))
        self.assertEqual(len(response.context['entries']), 6)

    def test_second_page_exists(self) -> None:
        response = self.client.get(
            reverse(URL_LIST), {'page': 2}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['entries']), 1)


class FormValidationTests(BaseDiaryTestCase):
    """Валидация обязательных полей."""

    def setUp(self) -> None:
        self.client.force_login(self.author)

    def test_entry_requires_title_and_content(self) -> None:
        response = self.client.post(
            reverse(URL_CREATE), {'title': '', 'content': ''}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(Entry.objects.count(), 0)


class InitRolesTests(TestCase):
    """Команда init_roles создаёт группы и права, идемпотентна."""

    def test_creates_groups_and_permissions(self) -> None:
        call_command('init_roles', verbosity=0)
        group = Group.objects.get(name='Модераторы')
        self.assertTrue(
            Group.objects.filter(name='Пользователи').exists()
        )
        self.assertTrue(
            group.permissions.filter(
                codename='view_all_entries'
            ).exists()
        )
        self.assertTrue(
            group.permissions.filter(codename='change_entry').exists()
        )

    def test_is_idempotent(self) -> None:
        call_command('init_roles', verbosity=0)
        call_command('init_roles', verbosity=0)
        self.assertEqual(
            Group.objects.filter(name='Модераторы').count(), 1
        )
