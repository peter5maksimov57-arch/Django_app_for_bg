from datetime import timedelta
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth.hashers import make_password
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from main.models import Dependence, Person, Transaction


class ElementAttributes(HTMLParser):
    def __init__(self, content, tag, attribute):
        super().__init__()
        self.tag = tag
        self.attribute = attribute
        self.values = []
        self.feed(content)

    def handle_starttag(self, tag, attrs):
        if tag == self.tag:
            value = dict(attrs).get(self.attribute)
            if value is not None:
                self.values.append(value)


@override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"]
)
class FamilyViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        def person(name, email, balance=0, role=""):
            return Person.objects.create(
                name=name,
                email=email,
                password=make_password("correct-password"),
                balance=balance,
                role=role,
            )

        cls.admin = person("Администратор", "admin@example.com", 9000)
        cls.member = person("Участник", "member@example.com", 4000)
        cls.sibling = person("Второй участник", "sibling@example.com", 2000)
        cls.outsider = person("Чужой админ", "outsider@example.com", role="Admin")
        cls.other_member = person("Чужой участник", "other@example.com")
        
        Dependence.objects.create(user_id_admin=cls.admin.id, user_id_sub=cls.member.id)
        Dependence.objects.create(user_id_admin=cls.admin.id, user_id_sub=cls.sibling.id)
        Dependence.objects.create(user_id_admin=cls.outsider.id, user_id_sub=cls.other_member.id)

        cls.current_time = timezone.now().replace(day=15, hour=12, minute=0)
        cls.previous_time = cls.current_time.replace(day=1) - timedelta(days=1)

        def transaction(owner, amount, kind, category, label, *, old=False, regular=False):
            return Transaction.objects.create(user_id=owner.id, amount=amount, type_tr=kind, category=category,
                res_or_sen=label, regullar=regular, time=cls.previous_time if old else cls.current_time,)

        transaction(cls.admin, 901, "Трата", "Продукты", "Секрет администратора")
        transaction(cls.admin, 1201, "Поступление", "Зарплата", "Работа администратора")
        
        cls.member_expense = transaction(cls.member, 100, "Трата", "Продукты", "Покупка участника")
        cls.member_regular = transaction( cls.member, 20, "Трата", "ЖКХ", "Подписка участника", regular=True)
        
        transaction(cls.member, 500, "Поступление", "Зарплата", "Работа участника")
        transaction(cls.member, 70, "Трата", "Развлечения", "Старый расход", old=True)
        transaction(cls.member, 200, "Поступление", "Зарплата", "Старый доход", old=True)
        transaction(cls.sibling, 333, "Трата", "Другое", "Секрет второго участника")
        transaction(cls.other_member, 777, "Трата", "Другое", "Секрет другой семьи")

    def login_as(self, person):
        session = self.client.session
        session["user_id"] = person.id
        session.save()

    def member_url(self, person=None):
        return reverse("family_member", kwargs={"member_id": (person or self.member).id})

    @staticmethod
    def attributes(response, tag, attribute):
        return ElementAttributes(response.content.decode(), tag, attribute).values

    def test_own_dashboard_keeps_account_data_and_create_form(self):
        self.login_as(self.admin)
        response = self.client.get(reverse("main_page"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user"], self.admin)
        self.assertEqual(response.context["account_user"], self.admin)
        self.assertFalse(response.context["viewing_member"])
        self.assertEqual(response.context["income"], 1201)
        self.assertEqual(response.context["outcome"], 901)
        self.assertIn(reverse("family"), self.attributes(response, "a", "href"))
        self.assertIn(reverse("create_tr"), self.attributes(response, "form", "action"))

    def test_admin_sees_complete_own_family_with_admin_first(self):
        self.login_as(self.admin)
        response = self.client.get(reverse("family"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "family.html")
        groups = response.context["family_groups"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["admin"], self.admin)
        self.assertTrue(groups[0]["can_view"])
        self.assertCountEqual(groups[0]["members"], [self.member, self.sibling])
        links = self.attributes(response, "a", "href")
        self.assertIn(self.member_url(), links)
        self.assertIn(self.member_url(self.sibling), links)
        self.assertContains(response, self.admin.name)
        self.assertContains(response, self.member.name)
        self.assertContains(response, self.sibling.name)
        self.assertNotContains(response, self.outsider.name)
        self.assertNotContains(response, self.other_member.name)
        html = response.content.decode()
        self.assertRegex(html, "♕")

    def test_member_sees_family_without_dashboard_links(self):
        self.login_as(self.member)
        response = self.client.get(reverse("family"))

        self.assertEqual(response.status_code, 200)
        group = response.context["family_groups"][0]
        self.assertEqual(group["admin"], self.admin)
        self.assertFalse(group["can_view"])
        self.assertCountEqual(group["members"], [self.member, self.sibling])
        links = self.attributes(response, "a", "href")
        for person in (self.admin, self.member, self.sibling):
            self.assertNotIn(self.member_url(person), links)
        self.assertNotContains(response, self.other_member.name)

    def test_no_relationships_shows_empty_family_without_unrelated_profiles(self):
        solo = Person.objects.create(name="Один", email="solo@example.com", password="unused", balance=0, role="Admin")
        self.login_as(solo)
        response = self.client.get(reverse("family"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["family_groups"], [])
        self.assertNotContains(response, self.admin.name)
        self.assertNotContains(response, self.member.name)

    def test_admin_and_subordinate_roles_are_scoped_to_each_family(self):
        Dependence.objects.create(user_id_admin=self.member.id, user_id_sub=self.other_member.id)
        self.login_as(self.member)
        response = self.client.get(reverse("family"))

        groups = response.context["family_groups"]
        self.assertEqual(groups[0]["admin"], self.member)
        self.assertTrue(groups[0]["can_view"])
        self.assertEqual(groups[0]["members"], [self.other_member])
        self.assertEqual(groups[1]["admin"], self.admin)
        self.assertFalse(groups[1]["can_view"])
        links = self.attributes(response, "a", "href")
        self.assertIn(self.member_url(self.other_member), links)
        self.assertNotIn(self.member_url(self.sibling), links)
        self.assertNotContains(response, self.outsider.name)

    def test_member_dashboard_uses_only_selected_account_data_and_is_read_only(self):
        self.login_as(self.admin)
        response = self.client.get(self.member_url())

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")
        self.assertEqual(response.context["user"], self.member)
        self.assertEqual(response.context["account_user"], self.admin)
        self.assertTrue(response.context["viewing_member"])
        self.assertEqual(response.context["income"], 500)
        self.assertEqual(response.context["outcome"], 120)
        self.assertEqual(response.context["inc_for_categories"], [("Продукты", 100), ("ЖКХ", 20)])
        self.assertEqual(response.context["analytics_income"], 500)
        self.assertEqual(response.context["analytics_expenses"], 120)
        self.assertTrue(all(tr.user_id == self.member.id for tr in response.context["all_transactions"]))
        self.assertTrue(all(tr.user_id == self.member.id for tr in response.context["last_tr"]))
        self.assertContains(response, "Подписка участника")
        for private_label in ("Секрет администратора", "Секрет второго участника", "Секрет другой семьи"):
            self.assertNotContains(response, private_label)
        self.assertNotIn(reverse("create_tr"), self.attributes(response, "form", "action"))
        self.assertIn(reverse("family"), self.attributes(response, "a", "href"))
        self.assertEqual(self.client.session["user_id"], self.admin.id)

    def test_refresh_and_filter_stay_on_selected_member_without_mutating_accounts(self):
        self.login_as(self.admin)
        count_before = Transaction.objects.count()
        for payload in ({"refresh_chart": "1"},
            {"type_tr": "Трата", "category": "Продукты", "res_or_sen": "", "regullar": "Все"},):
            with self.subTest(payload=payload):
                response = self.client.post(self.member_url(), payload)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["user"], self.member)
                self.assertEqual(response.context["account_user"], self.admin)
                self.assertEqual(response.context["dashboard_url"], self.member_url())
                self.assertIn(self.member_url(), self.attributes(response, "form", "action"))
                self.assertNotIn(reverse("main_page"), self.attributes(response, "form", "action"))
                self.assertEqual(self.client.session["user_id"], self.admin.id)
        self.assertEqual(list(response.context["all_transactions"]), [self.member_expense])
        self.assertEqual(Transaction.objects.count(), count_before)
        self.member.refresh_from_db()
        self.admin.refresh_from_db()
        self.assertEqual(self.member.balance, 4000)
        self.assertEqual(self.admin.balance, 9000)

    def test_month_navigation_keeps_member_and_uses_selected_month(self):
        self.login_as(self.admin)
        response = self.client.get(self.member_url(),
            {"tab": "analytics", "month": self.previous_time.strftime("%Y-%m")},)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["analytics_income"], 200)
        self.assertEqual(response.context["analytics_expenses"], 70)
        self.assertEqual(sum(p["amount"] for p in response.context["analytics_income_points"]), 200)
        self.assertEqual(sum(p["amount"] for p in response.context["analytics_expense_points"]), 70)
        
        month_links = [urlsplit(href) for href in self.attributes(response, "a", "href")
            if "month" in parse_qs(urlsplit(href).query)]
        self.assertGreaterEqual(len(month_links), 2)
        
        for link in month_links:
            self.assertIn(link.path, ("", self.member_url()))
        self.assertEqual(self.client.session["user_id"], self.admin.id)

    def test_return_to_own_dashboard_restores_admin_data(self):
        self.login_as(self.admin)
        self.client.get(self.member_url())
        self.client.get(reverse("family"))
        response = self.client.get(reverse("main_page"))

        self.assertEqual(response.context["user"], self.admin)
        self.assertFalse(response.context["viewing_member"])
        self.assertEqual(response.context["outcome"], 901)

    def test_non_admin_sibling_and_unrelated_admin_cannot_view_member(self):
        for actor, target in (
            (self.member, self.admin),
            (self.member, self.sibling),
            (self.sibling, self.member),
            (self.outsider, self.member),
            (self.admin, self.other_member),
        ):
            self.login_as(actor)
            with self.subTest(actor=actor.name, target=target.name):
                response = self.client.get(self.member_url(target))
                self.assertEqual(response.status_code, 403)
                self.assertTemplateUsed(response, "status.html")
                self.assertEqual(self.client.session["user_id"], actor.id)

    def test_revoked_relationship_is_rechecked_for_get_and_post(self):
        self.login_as(self.admin)
        self.assertEqual(self.client.get(self.member_url()).status_code, 200)
        Dependence.objects.filter(user_id_admin=self.admin.id, user_id_sub=self.member.id).delete()

        self.assertEqual(self.client.get(self.member_url()).status_code, 403)
        self.assertEqual(self.client.post(self.member_url(), {"refresh_chart": "1"}).status_code, 403)

    def test_missing_member_does_not_raise_server_error(self):
        self.login_as(self.admin)
        response = self.client.get(reverse("family_member", kwargs={"member_id": 999999}))
        self.assertIn(response.status_code, (403, 404))

    def test_unauthenticated_family_pages_show_login_status(self):
        for url in (reverse("family"), self.member_url()):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertTemplateUsed(response, "status.html")
                self.assertContains(response, "Сессия истекла")
                self.assertNotContains(response, "Покупка участника")

    def test_deleted_session_account_does_not_raise_server_error(self):
        session = self.client.session
        session["user_id"] = 999999
        session.save()
        response = self.client.get(reverse("family"))

        self.assertTemplateUsed(response, "status.html")
        self.assertNotIn("user_id", self.client.session)

    def test_wrong_password_cannot_authenticate_as_family_admin(self):
        response = self.client.post("/", {"email": self.admin.email, "password": "wrong-password"})

        self.assertContains(response, "Неверный пароль")
        self.assertNotIn("user_id", self.client.session)
        response = self.client.get(self.member_url())
        self.assertTemplateUsed(response, "status.html")
        self.assertNotContains(response, "Покупка участника")
