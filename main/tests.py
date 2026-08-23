from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse

from main.models import Person


class FormErrorTests(TestCase):
    def setUp(self):
        self.user = Person.objects.create(
            name="Тест",
            email="test@example.com",
            password=make_password("correct-password"),
            balance=0,
            role="",
        )

    def test_wrong_password_stays_on_login_page(self):
        response = self.client.post(
            "/",
            {"email": self.user.email, "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Неверный пароль")
        self.assertContains(response, 'class="form-errors"')

    def test_invalid_registration_stays_on_form(self):
        response = self.client.post(
            reverse("registration"),
            {"name": "x", "email": "bad", "password": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="form-errors"')

    def test_duplicate_email_stays_on_registration_page(self):
        response = self.client.post(
            reverse("registration"),
            {"name": "Другой", "email": self.user.email, "password": "password123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "уже существует")

    def test_wrong_code_stays_on_code_page(self):
        session = self.client.session
        session["reg_email"] = "new@example.com"
        session["verification_code"] = "123456"
        session.save()

        response = self.client.post(reverse("reg_code"), {"us_code": "654321"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Введён неверный код подтверждения")
        self.assertContains(response, 'class="form-errors"')
