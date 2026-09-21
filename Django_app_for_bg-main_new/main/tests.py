from django.contrib.auth.hashers import make_password
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from main.models import Person, Transaction


@override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"]
)
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


@override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"]
)
class PageFlowTests(TestCase):
    def setUp(self):
        self.user = Person.objects.create(
            name="Тест",
            email="test@example.com",
            password=make_password("correct-password"),
            balance=1250,
            role="",
        )

    def test_successful_login_opens_dashboard(self):
        response = self.client.post(
            "/",
            {"email": self.user.email, "password": "correct-password"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")
        self.assertContains(response, "Статистика")
        self.assertContains(response, "Переводы")
        self.assertContains(response, "Все операции")

    def test_chart_contains_only_current_month_expenses(self):
        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

        Transaction.new_tr(self.user.id, 100, "Трата", "Продукты", "Магазин")
        Transaction.new_tr(self.user.id, 500, "Поступление", "Зарплата", "Работа")
        old_expense = Transaction.new_tr(
            self.user.id, 300, "Трата", "Развлечения", "Кино"
        )
        previous_month = timezone.now().replace(day=1) - timedelta(days=1)
        Transaction.objects.filter(id=old_expense.id).update(time=previous_month)

        response = self.client.get(reverse("main_page"))

        self.assertEqual(response.context["outcome"], 100)
        self.assertEqual(response.context["inc_for_categories"], [("Продукты", 100)])
        self.assertEqual(response.context["expense_chart"][0]["category"], "Продукты")
        self.assertContains(response, "conic-gradient")
        self.assertContains(response, "Обновить диаграмму")
        self.assertNotContains(response, "dashboard.js")

        old_gradient = response.context["expense_chart_gradient"]
        Transaction.new_tr(self.user.id, 50, "Трата", "Развлечения", "Кино")

        refreshed_response = self.client.post(
            reverse("main_page"),
            {"refresh_chart": "1"},
        )

        self.assertEqual(refreshed_response.status_code, 200)
        self.assertEqual(refreshed_response.context["outcome"], 150)
        self.assertNotEqual(
            refreshed_response.context["expense_chart_gradient"],
            old_gradient,
        )
        self.assertContains(
            refreshed_response,
            'id="tab-statistics" checked',
        )

    def test_operations_tab_filters_existing_transactions(self):
        session = self.client.session
        session["user_id"] = self.user.id
        session.save()

        Transaction.new_tr(self.user.id, 100, "Трата", "Продукты", "Магазин")
        Transaction.new_tr(self.user.id, 500, "Поступление", "Зарплата", "Работа")

        response = self.client.post(
            reverse("main_page"),
            {
                "type_tr": "Трата",
                "category": "Все",
                "res_or_sen": "",
                "regullar": "Все",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Магазин")
        self.assertNotContains(response, "Работа")
        self.assertContains(response, 'id="tab-operations" checked')

    def test_registration_completion_has_return_button(self):
        session = self.client.session
        session["reg_email"] = "new@example.com"
        session["reg_name"] = "Новый"
        session["reg_password"] = "password123"
        session["verification_code"] = "123456"
        session.save()

        response = self.client.post(reverse("reg_code"), {"us_code": "123456"})

        self.assertTemplateUsed(response, "status.html")
        self.assertContains(response, "Регистрация завершена")
        self.assertContains(response, "Перейти ко входу")

    def test_expired_session_has_return_button(self):
        response = self.client.get(reverse("reg_code"))

        self.assertTemplateUsed(response, "status.html")
        self.assertContains(response, "Сессия истекла")
        self.assertContains(response, "Вернуться к регистрации")

    def test_password_change_has_return_button(self):
        session = self.client.session
        session["res_email"] = self.user.email
        session.save()

        response = self.client.post(reverse("new_pas"), {"password": "new-password"})

        self.assertTemplateUsed(response, "status.html")
        self.assertContains(response, "Пароль изменён")
        self.assertContains(response, "Перейти ко входу")
