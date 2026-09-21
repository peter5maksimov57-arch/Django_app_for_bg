import re
from unittest.mock import patch

from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from main.models import Dependence, Person, Transaction


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
)
class FamilyManagementTests(TestCase):
    def setUp(self):
        self.admin = self.person('Администратор')
        self.member = self.person('Участник')
        self.sibling = self.person('Второй участник')
        self.outsider = self.person('Посторонний')
        Dependence.add_dependence(self.admin.id, self.member.id)
        Dependence.add_dependence(self.admin.id, self.sibling.id)
        self.login_as(self.admin)

    def person(self, name):
        return Person.objects.create(
            name=name, email=f'user{Person.objects.count()}@example.com',
            password='', balance=100, role='',
        )

    def login_as(self, person, client=None):
        session = (client or self.client).session
        session['user_id'] = person.id
        session.save()

    def test_admin_can_invite_more_members_and_has_no_leave_button(self):
        response = self.client.get(reverse('family'))
        self.assertContains(response, 'Пригласить участника')
        self.assertContains(response, reverse('family_remove', args=[self.member.id]))
        self.assertNotContains(response, 'Выйти из семьи')
        url = reverse('family_create')
        response = self.client.get(url)
        self.assertContains(response, 'Приглашение участника')
        self.assertNotContains(response, 'name="code"')
        self.assertContains(response, 'name="email"')
        response = self.client.post(url, {'action': 'send', 'email': self.outsider.email})
        self.assertContains(response, 'name="code"')
        code = re.search(r'Код приглашения: (\d{6})', mail.outbox[-1].body).group(1)
        response = self.client.post(url, {'action': 'confirm', 'email': self.outsider.email, 'code': code})
        self.assertRedirects(response, reverse('family'))
        self.assertEqual(Dependence.objects.filter(user_id_admin=self.admin.id).count(), 3)
        self.assertContains(self.client.get(reverse('family')), 'Пригласить участника')

    def test_member_can_create_own_family_without_gaining_rights_in_original_family(self):
        self.login_as(self.member)
        response = self.client.get(reverse('family'))
        self.assertContains(response, 'Выйти из семьи')
        self.assertContains(response, 'Создать семью')
        self.assertNotContains(response, 'Пригласить участника')
        self.assertNotContains(response, reverse('family_remove', args=[self.sibling.id]))
        url = reverse('family_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="code"')
        response = self.client.post(url, {'action': 'send', 'email': self.outsider.email})
        self.assertContains(response, 'name="code"')
        self.assertFalse(Dependence.objects.filter(user_id_admin=self.member.id).exists())
        code = re.search(r'Код приглашения: (\d{6})', mail.outbox[-1].body).group(1)
        response = self.client.post(url, {'action': 'confirm', 'email': self.outsider.email, 'code': code})
        self.assertRedirects(response, reverse('family'))
        self.member.refresh_from_db()
        self.assertEqual(self.member.role, 'Subordinate/Admin')
        self.assertTrue(Dependence.objects.filter(user_id_admin=self.admin.id, user_id_sub=self.member.id).exists())
        family = self.client.get(reverse('family'))
        self.assertEqual(
            {group['admin'].id: group['can_view'] for group in family.context['family_groups']},
            {self.member.id: True, self.admin.id: False},
        )
        self.assertContains(family, 'Пригласить участника')
        self.assertNotContains(family, 'Создать семью')
        self.assertEqual(self.client.get(reverse('family_member', args=[self.outsider.id])).status_code, 200)
        self.assertEqual(self.client.get(reverse('family_member', args=[self.sibling.id])).status_code, 403)
        self.assertEqual(self.client.post(reverse('family_remove', args=[self.sibling.id])).status_code, 403)
        self.login_as(self.admin)
        self.assertEqual(self.client.get(reverse('family_member', args=[self.outsider.id])).status_code, 403)
        self.login_as(self.member)
        self.client.post(reverse('family_remove', args=[self.outsider.id]))
        self.member.refresh_from_db()
        self.assertEqual(self.member.role, 'Subordinate')
        self.assertContains(self.client.get(reverse('family')), 'Создать семью')

    def test_admin_removes_only_link_and_loses_access_immediately(self):
        entry = Transaction.new_tr(self.member.id, 20, 'Трата', 'Продукты', 'Магазин')
        with patch.object(Dependence, 'delete_dependence', wraps=Dependence.delete_dependence) as delete:
            response = self.client.post(reverse('family_remove', args=[self.member.id]))
            delete.assert_called_once_with(self.admin.id, self.member.id)
        self.assertRedirects(response, reverse('family'))
        self.assertTrue(Transaction.objects.filter(id=entry.id).exists())
        self.member.refresh_from_db()
        self.assertEqual(self.member.role, '')
        self.assertEqual(self.member.balance, 100)
        self.assertEqual(self.client.get(reverse('family_member', args=[self.member.id])).status_code, 403)
        self.assertTrue(Dependence.objects.filter(user_id_admin=self.admin.id, user_id_sub=self.sibling.id).exists())

    def test_member_leaves_without_removing_siblings(self):
        self.login_as(self.member)
        with patch.object(Dependence, 'delete_dependence', wraps=Dependence.delete_dependence) as delete:
            response = self.client.post(reverse('family_leave', args=[self.admin.id]))
            delete.assert_called_once_with(self.admin.id, self.member.id)
        self.assertRedirects(response, reverse('family'))
        self.assertContains(self.client.get(reverse('family')), 'Создать семью')
        self.assertTrue(Dependence.objects.filter(user_id_sub=self.sibling.id).exists())
        self.login_as(self.admin)
        self.assertEqual(self.client.get(reverse('family_member', args=[self.member.id])).status_code, 403)

    def test_unauthorized_removal_self_removal_and_repeated_removal_fail(self):
        for actor in [self.member, self.outsider]:
            self.login_as(actor)
            self.assertEqual(self.client.post(reverse('family_remove', args=[self.sibling.id])).status_code, 403)
        self.login_as(self.admin)
        self.assertEqual(self.client.post(reverse('family_remove', args=[self.admin.id])).status_code, 403)
        self.assertEqual(self.client.post(reverse('family_leave', args=[self.admin.id])).status_code, 403)
        self.client.post(reverse('family_remove', args=[self.member.id]))
        self.assertEqual(self.client.post(reverse('family_remove', args=[self.member.id])).status_code, 403)

    def test_post_and_csrf_required_and_guest_cannot_remove(self):
        remove_url = reverse('family_remove', args=[self.member.id])
        leave_url = reverse('family_leave', args=[self.admin.id])
        for url in [remove_url, leave_url]:
            self.assertEqual(self.client.get(url).status_code, 405)
        csrf_client = Client(enforce_csrf_checks=True)
        self.login_as(self.admin, csrf_client)
        self.assertEqual(csrf_client.post(remove_url).status_code, 403)
        self.client.session.flush()
        self.assertContains(self.client.post(remove_url), 'Сессия истекла')
        self.assertEqual(Dependence.objects.count(), 2)

    def test_last_member_removal_allows_new_family_creation(self):
        for member in [self.member, self.sibling]:
            self.client.post(reverse('family_remove', args=[member.id]))
        self.assertEqual(self.client.get(reverse('family_create')).status_code, 200)
        self.assertContains(self.client.get(reverse('family')), 'Создать семью')
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.role, '')

    def test_duplicate_links_are_all_revoked(self):
        Dependence.objects.create(user_id_admin=self.admin.id, user_id_sub=self.member.id)
        self.client.post(reverse('family_remove', args=[self.member.id]))
        self.assertFalse(Dependence.objects.filter(user_id_admin=self.admin.id, user_id_sub=self.member.id).exists())
