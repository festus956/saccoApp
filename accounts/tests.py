from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from decimal import Decimal

from core.models import Member

from .models import MemberBalance


class MemberBalanceModelTests(APITestCase):
    def setUp(self):
        self.member = Member.objects.create(
            first_name="Jane",
            last_name="Doe",
            member_no="M001",
            id_number="12345678",
            phone_number="0700000000",
            email="jane@example.com",
        )
        self.balance = MemberBalance.objects.create(
            member=self.member,
            share=1000,
            deposits=5000,
            loans_balance=2000,
        )

    def test_str_representation(self):
        self.assertEqual(str(self.balance), "Jane Doe - 1000 - 5000")

    def test_get_a_member_summary(self):
        summary = self.balance.get_a_member_summary()
        self.assertEqual(summary["member"], "M001")
        self.assertEqual(summary["max_loan_amount"], 5000 * 3)
        self.assertEqual(summary["loan_eligibility"], 5000 * 3 - 2000)


    def test_get_sacco_stats(self):
        stats = MemberBalance.get_sacco_stats()
        self.assertEqual(stats["total_members"], 1)
        self.assertEqual(stats["total_deposits"], 5000)
        self.assertEqual(stats["total_loans"], 2000)
        self.assertEqual(stats["total_shares"], 1000)
        self.assertEqual(stats["loans_over_deposits"], Decimal("2000") / Decimal("5000"))

    def test_get_sacco_stats_with_no_records(self):
        MemberBalance.objects.all().delete()
        stats = MemberBalance.get_sacco_stats()
        self.assertEqual(stats["total_members"], 0)
        self.assertEqual(stats["total_deposits"], 0)
        self.assertEqual(stats["loans_over_deposits"], 0)

    def test_negative_share_rejected_by_validator(self):
        invalid_balance = MemberBalance(
            member=self.member, share=-100, deposits=0, loans_balance=0
        )
        with self.assertRaises(Exception):
            invalid_balance.full_clean()


class MemberBalanceAPITests(APITestCase):
    def setUp(self):
        self.member = Member.objects.create(
            first_name="John",
            last_name="Smith",
            member_no="M002",
            id_number="87654321",
            phone_number="0711111111",
            email="john@example.com",
        )
        self.staff_user = User.objects.create_user(
            username="staffuser", password="testpass123", is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username="regularuser", password="testpass123", is_staff=False
        )

    def test_create_balance_requires_authentication(self):
        url = reverse("accounts:member_balance_save")
        response = self.client.post(url, {"member_uid": "M002", "share": 100, "deposits": 500, "loans_balance": 0})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_cannot_create_balance(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse("accounts:member_balance_save")
        response = self.client.post(url, {"member_uid": "M002", "share": 100, "deposits": 500, "loans_balance": 0})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        print(response.data)

    def test_staff_can_create_balance(self):
        self.client.force_authenticate(user=self.staff_user)
        url = reverse("accounts:member_balance_save")
        response = self.client.post(
            url, {"member_uid": "M002", "share": 100, "deposits": 500, "loans_balance": 0}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(MemberBalance.objects.filter(member=self.member).exists())

    def test_create_balance_missing_member_uid(self):
        self.client.force_authenticate(user=self.staff_user)
        url = reverse("accounts:member_balance_save")
        response = self.client.post(url, {"share": 100, "deposits": 500, "loans_balance": 0})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_balance_unknown_member(self):
        self.client.force_authenticate(user=self.staff_user)
        url = reverse("accounts:member_balance_save")
        response = self.client.post(
            url, {"member_uid": "DOES-NOT-EXIST", "share": 100, "deposits": 500, "loans_balance": 0}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_balance_rejects_negative_amount(self):
        self.client.force_authenticate(user=self.staff_user)
        url = reverse("accounts:member_balance_save")
        response = self.client.post(
            url, {"member_uid": "M002", "share": -50, "deposits": 500, "loans_balance": 0}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_existing_balance_via_put(self):
        MemberBalance.objects.create(member=self.member, share=100, deposits=500, loans_balance=0)
        self.client.force_authenticate(user=self.staff_user)
        url = reverse("accounts:member_balance_save")
        response = self.client.put(url, {"member_uid": "M002", "deposits": 750})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["deposits"], "750.00")

    def test_get_balance_by_member_uid(self):
        MemberBalance.objects.create(member=self.member, share=100, deposits=500, loans_balance=0)
        self.client.force_authenticate(user=self.staff_user)
        url = reverse("accounts:member_balance_by_uid", kwargs={"member_uid": "M002"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["member"]["fullname"], "John Smith")

    def test_get_balance_not_found(self):
        self.client.force_authenticate(user=self.staff_user)
        url = reverse("accounts:member_balance_by_uid", kwargs={"member_uid": "NOPE"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)