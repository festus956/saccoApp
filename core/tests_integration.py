"""
Cross-app integration tests: core <-> accounts hand-off.

Place at: core/tests_integration.py
Run with: python3 manage.py test core.tests_integration
"""
import unittest

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Member

User = get_user_model()

PASSWORD = "StrongPass123!"


def make_member_user(username="grace", member_no="7"):
    """An active login account linked to an active Member."""
    user = User.objects.create_user(
        username=username, password=PASSWORD, email=f"{username}@example.com"
    )
    member = Member.objects.create(
        first_name="Grace",
        last_name="Wanjiku",
        member_no=member_no,
        id_number=f"ID{member_no}",
        phone_number=f"07000000{member_no}",
        email=f"{username}@example.com",
        status=Member.STATUS_ACTIVE,
        user=user,
    )
    return user, member


class LoginRedirectTests(TestCase):
    """Login sends each role to the right place."""

    def setUp(self):
        self.member_user, self.member = make_member_user()
        self.staff_user = User.objects.create_user(
            username="staffer", password=PASSWORD, is_staff=True
        )

    # NOTE: if these two fail on the form (not the redirect), your login
    # form may use different field names than "username"/"password".
    def test_member_login_redirects_to_home(self):
        response = self.client.post(
            reverse("loginpage"),
            {"username": "grace", "password": PASSWORD},
        )
        self.assertRedirects(response, reverse("home"))

    def test_staff_login_redirects_to_accounts_page(self):
        response = self.client.post(
            reverse("loginpage"),
            {"username": "staffer", "password": PASSWORD},
        )
        self.assertRedirects(
            response,
            reverse("accounts:member_balance"),
            fetch_redirect_response=False,
        )


class MemberPagesTests(TestCase):
    """A logged-in member sees their own data."""

    def setUp(self):
        self.user, self.member = make_member_user()
        self.client.force_login(self.user)

    def test_home_shows_dashboard_and_name(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Member Dashboard")
        self.assertContains(response, "Grace")

    def test_loans_page_loads(self):
        response = self.client.get(reverse("loans"))
        self.assertEqual(response.status_code, 200)


class StaffPageTests(TestCase):
    """Staff land on the accounts page using the right template."""

    def setUp(self):
        self.staff = User.objects.create_user(
            username="staffer", password=PASSWORD, is_staff=True
        )
        self.client.force_login(self.staff)

    def test_staff_can_open_member_balance_page(self):
        response = self.client.get(reverse("accounts:member_balance"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/member_balance.html")


class AnonymousRedirectTests(TestCase):
    """Anonymous visitors are sent to /login/ from every protected page."""

    def _assert_login_redirect(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"), response.url)

    def test_home_redirects(self):
        self._assert_login_redirect(reverse("home"))

    def test_loans_redirects(self):
        self._assert_login_redirect(reverse("loans"))

    def test_member_balance_page_redirects(self):
        self._assert_login_redirect(reverse("accounts:member_balance"))


class NonStaffApiAccessTests(TestCase):
    """Non-staff users are refused by the staff API."""

    def setUp(self):
        self.user, self.member = make_member_user()

    def test_member_refused_by_balance_api(self):
        self.client.force_login(self.user)
        url = reverse("accounts:member_balance_by_uid", args=[self.member.member_no])
        response = self.client.get(url)
        self.assertIn(response.status_code, (401, 403))

    def test_anonymous_refused_by_balance_api(self):
        url = reverse("accounts:member_balance_by_uid", args=[self.member.member_no])
        response = self.client.get(url)
        self.assertIn(response.status_code, (401, 403))


class KnownGapTests(TestCase):
    """
    Documents the known security gap: a plain member can open the staff
    page. Marked expectedFailure so the suite stays green today.
    After you add @staff_member_required, this will report
    "unexpected success" -- that is your cue to delete the decorator.
    """

    @unittest.expectedFailure
    def test_member_refused_by_staff_balance_page(self):
        user, _ = make_member_user()
        self.client.force_login(user)
        response = self.client.get(reverse("accounts:member_balance"))
        self.assertNotEqual(response.status_code, 200)