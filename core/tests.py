from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .forms import MemberRegistrationForm, generate_member_no
from .models import Loan, Member

User = get_user_model()


class MemberRegistrationFormTests(TestCase):
    def test_creates_inactive_user_and_member(self):
        form = MemberRegistrationForm(data={
            "username": "newmember",
            "email": "newmember@example.com",
            "first_name": "Jane",
            "last_name": "Doe",
            "id_number": "12345678",
            "phone_number": "0712345678",
            "password1": "StrongPass!23",
            "password2": "StrongPass!23",
        })
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()

        self.assertFalse(user.is_active)
        member = Member.objects.get(user=user)
        self.assertEqual(member.status, Member.STATUS_INACTIVE)
        self.assertEqual(member.first_name, "Jane")

    def test_rejects_duplicate_id_number(self):
        existing_user = User.objects.create_user(username="existing", password="pass12345")
        Member.objects.create(
            user=existing_user,
            first_name="Alex",
            last_name="Gacheru",
            member_no="1",
            id_number="12345678",
            phone_number="0700000000",
            email="alex@example.com",
        )

        form = MemberRegistrationForm(data={
            "username": "dupe",
            "email": "dupe@example.com",
            "first_name": "Copy",
            "last_name": "Cat",
            "id_number": "12345678",
            "phone_number": "0711111111",
            "password1": "StrongPass!23",
            "password2": "StrongPass!23",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("id_number", form.errors)


class GenerateMemberNoTests(TestCase):
    def test_first_member_gets_no_1(self):
        self.assertEqual(generate_member_no(), "1")

    def test_increments_from_highest_existing(self):
        user = User.objects.create_user(username="m5", password="pass12345")
        Member.objects.create(
            user=user, first_name="A", last_name="B", member_no="5",
            id_number="000", phone_number="000", email="a@b.com",
        )
        self.assertEqual(generate_member_no(), "6")


class LoginRedirectTests(TestCase):
    def setUp(self):
        self.member_user = User.objects.create_user(
            username="member1", password="pass12345", is_active=True
        )
        self.member = Member.objects.create(
            user=self.member_user, first_name="Festus", last_name="Mwangi",
            member_no="2", id_number="111", phone_number="222",
            email="festus@example.com", status=Member.STATUS_ACTIVE,
        )
        self.staff_user = User.objects.create_user(
            username="staffer", password="pass12345", is_active=True, is_staff=True
        )

    def test_inactive_user_cannot_log_in(self):
        User.objects.create_user(username="pending", password="pass12345", is_active=False)
        response = self.client.post(reverse("loginpage"), {
            "username": "pending", "password": "pass12345",
        })
        self.assertEqual(response.status_code, 200)  # re-renders login, no redirect
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_member_login_redirects_home(self):
        response = self.client.post(reverse("loginpage"), {
            "username": "member1", "password": "pass12345",
        })
        self.assertRedirects(response, reverse("home"))

    def test_staff_login_redirects_to_member_balance(self):
        response = self.client.post(reverse("loginpage"), {
            "username": "staffer", "password": "pass12345",
        })
        self.assertRedirects(response, reverse("accounts:member_balance"))


class HomeViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="member2", password="pass12345")
        self.member = Member.objects.create(
            user=self.user, first_name="Grace", last_name="Wanjiru",
            member_no="3", id_number="333", phone_number="444",
            email="grace@example.com", status=Member.STATUS_ACTIVE,
        )

    def test_home_requires_login(self):
        response = self.client.get(reverse("home"))
        self.assertNotEqual(response.status_code, 200)  # redirected to login

    def test_home_shows_member_details(self):
        self.client.login(username="member2", password="pass12345")
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Grace")
        self.assertContains(response, "3")

    def test_home_handles_user_with_no_member(self):
        User.objects.create_user(username="orphan", password="pass12345")
        self.client.login(username="orphan", password="pass12345")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No member profile is linked")


class LoansViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="member3", password="pass12345")
        self.member = Member.objects.create(
            user=self.user, first_name="Peter", last_name="Otieno",
            member_no="4", id_number="555", phone_number="666",
            email="peter@example.com", status=Member.STATUS_ACTIVE,
        )
        self.client.login(username="member3", password="pass12345")

    def test_loans_page_empty_state(self):
        response = self.client.get(reverse("loans"))
        self.assertContains(response, "No loan records found")

    def test_loans_page_lists_own_loans(self):
        Loan.objects.create(
            member=self.member, amount_applied=10000, amount_approved=8000,
            interest_rate=10, status=Loan.STATUS_APPROVED,
        )
        response = self.client.get(reverse("loans"))
        self.assertContains(response, "8000")
        self.assertContains(response, "Approved")


class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="resetme", password="OldPass!23",
            email="resetme@example.com", is_active=True,
        )

    def test_password_reset_sends_email(self):
        response = self.client.post(reverse("password_reset"), {
            "email": "resetme@example.com",
        })
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("saccoApp", mail.outbox[0].subject)