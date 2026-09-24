import re
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from main.models import Dependence, Person


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])

class FamilyInvitationTests(TestCase):
    def setUp(self):
        self.admin = self.person('Создатель', 'creator@example.com')
        self.member = self.person('Участник', 'member@example.com')
        self.url = reverse('family_create')
        self.login_as(self.admin)

    def person(self, name, email):
        return Person.objects.create(name=name, email=email, password='', balance=0, role='')

    def login_as(self, person):
        session = self.client.session
        session['user_id'] = person.id
        session.save()

    def invite(self):
        response = self.client.post(self.url, {'action': 'send', 'email': self.member.email})
        self.assertContains(response, 'Код отправлен получателю')
        return re.search(r'Код приглашения: (\d{6})', mail.outbox[-1].body).group(1)

    def confirm(self, code, email=None):
        return self.client.post(self.url, {
            'action': 'confirm', 'email': email or self.member.email, 'code': code,
        })

    def test_first_family_shows_code_only_after_invitation(self):
        self.assertContains(self.client.get(reverse('family')), 'Создать семью')
        response = self.client.get(self.url)
        self.assertContains(response, 'name="email"')
        self.assertNotContains(response, 'name="code"')
        self.assertNotContains(response, 'value="confirm"')
        self.invite()
        response = self.client.get(self.url)
        self.assertContains(response, 'name="code"')
        self.assertContains(response, 'Подтвердить и создать семью')

    def test_invitation_requires_consent_before_granting_access(self):
        code = self.invite()
        self.assertEqual(mail.outbox[0].to, [self.member.email])
        self.assertIn(self.admin.name, mail.outbox[0].body)
        self.assertIn('просматривать ваш баланс', mail.outbox[0].body)
        self.assertFalse(Dependence.objects.exists())
        self.assertNotIn(code, str(self.client.session['family_invitation']))
        self.assertEqual(self.client.get(reverse('family_member', args=[self.member.id])).status_code, 403)

        response = self.confirm(code)
        self.assertRedirects(response, reverse('family'))
        self.admin.refresh_from_db()
        self.member.refresh_from_db()
        self.assertEqual(self.admin.role, 'Admin')
        self.assertEqual(self.member.role, 'Subordinate')
        self.assertNotIn('family_invitation', self.client.session)
        self.assertEqual(self.client.session['user_id'], self.admin.id)
        family = self.client.get(reverse('family'))
        self.assertContains(family, '♕')
        self.assertContains(family, reverse('family_member', args=[self.member.id]))
        self.assertNotContains(family, 'Создать семью')
        self.assertEqual(self.client.get(reverse('family_member', args=[self.member.id])).status_code, 200)
        self.login_as(self.member)
        self.assertContains(self.client.get(reverse('family')), self.admin.name)
        self.assertEqual(self.client.get(reverse('family_member', args=[self.admin.id])).status_code, 403)

    def test_wrong_code_and_attempt_limit(self):
        code = self.invite()
        wrong_code = '000000' if code != '000000' else '111111'
        for _ in range(5):
            self.confirm(wrong_code)
        self.assertNotIn('family_invitation', self.client.session)
        self.assertFalse(Dependence.objects.exists())
        self.assertContains(self.confirm(code), 'Сначала отправьте приглашение')

    def test_expired_code_is_rejected(self):
        code = self.invite()
        session = self.client.session
        invitation = session['family_invitation']
        invitation['expires_at'] = 0
        session['family_invitation'] = invitation
        session.save()
        self.assertContains(self.confirm(code), 'Сначала отправьте приглашение')
        self.assertFalse(Dependence.objects.exists())

    def test_code_is_bound_to_sender_and_recipient(self):
        other = self.person('Другой', 'other@example.com')
        code = self.invite()
        self.assertContains(self.confirm(code, other.email), 'для другого адреса')
        self.login_as(other)
        self.assertContains(self.confirm(code), 'Сначала отправьте приглашение')
        self.assertFalse(Dependence.objects.exists())

    def test_invalid_self_unknown_and_ambiguous_email_cannot_receive_invite(self):
        for email in ['not-an-email', self.admin.email, 'missing@example.com']:
            response = self.client.post(self.url, {'action': 'send', 'email': email})
            self.assertTrue(response.context['form'].errors)
        self.person('Дубликат', self.member.email.upper())
        response = self.client.post(self.url, {'action': 'send', 'email': self.member.email})
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(Dependence.objects.exists())

    def test_resend_throttle_and_old_code_invalidation(self):
        with patch('main.mail.secrets.randbelow', side_effect=[123456, 234567]):
            old_code = self.invite()
            response = self.client.post(self.url, {'action': 'send', 'email': self.member.email})
            self.assertContains(response, 'через минуту')
            self.assertEqual(len(mail.outbox), 1)
            session = self.client.session
            session['family_invitation_sent_at'] = 0
            session.save()
            new_code = self.invite()
        self.assertContains(self.confirm(old_code), 'Неверный код')
        self.assertRedirects(self.confirm(new_code), reverse('family'))

    def test_email_failure_leaves_no_invitation_or_link(self):
        with patch('main.mail.send_family_code', side_effect=OSError('SMTP unavailable')):
            response = self.client.post(self.url, {'action': 'send', 'email': self.member.email})
        self.assertContains(response, 'Не удалось отправить письмо')
        self.assertNotContains(response, 'name="code"')
        self.assertNotIn('family_invitation', self.client.session)
        self.assertFalse(Dependence.objects.exists())

    def test_replay_and_direct_confirmation_do_not_create_links(self):
        self.assertContains(self.confirm('123456'), 'Сначала отправьте приглашение')
        code = self.invite()
        self.confirm(code)
        self.assertContains(self.confirm(code), 'уже состоит')
        self.assertEqual(Dependence.objects.count(), 1)

    def test_existing_admin_can_join_while_retaining_own_family_rights(self):
        third = self.person('Ребёнок', 'child@example.com')
        Dependence.add_dependence(self.member.id, third.id)
        code = self.invite()
        self.assertFalse(Dependence.objects.filter(user_id_admin=self.admin.id).exists())
        self.assertRedirects(self.confirm(code), reverse('family'))
        self.assertEqual(len(mail.outbox), 1)
        self.member.refresh_from_db()
        self.assertEqual(self.member.role, 'Subordinate/Admin')

        self.assertEqual(self.client.get(reverse('family_member', args=[third.id])).status_code, 403)
        self.assertEqual(self.client.get(reverse('family_member', args=[self.member.id])).status_code, 200)
        self.login_as(self.member)
        response = self.client.get(reverse('family'))
        self.assertEqual({group['admin'].id: group['can_view'] for group in response.context['family_groups']}, {self.admin.id: False, self.member.id: True})
        
        self.assertEqual(self.client.get(reverse('family_member', args=[third.id])).status_code, 200)
        self.assertEqual(self.client.get(reverse('family_member', args=[self.admin.id])).status_code, 403)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertRedirects(self.client.post(reverse('family_leave', args=[self.admin.id])), reverse('family'))
        self.member.refresh_from_db()
        self.assertEqual(self.member.role, 'Admin')
        self.assertTrue(Dependence.objects.filter(user_id_admin=self.member.id, user_id_sub=third.id).exists())
        self.assertFalse(Dependence.objects.filter(user_id_admin=self.admin.id).exists())

    def test_session_required_for_get_and_post(self):
        self.client.session.flush()
        for response in [self.client.get(self.url), self.client.post(self.url, {
            'action': 'send', 'email': self.member.email,
        })]:
            self.assertContains(response, 'Сессия истекла')
        self.assertEqual(len(mail.outbox), 0)
