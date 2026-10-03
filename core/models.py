from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class Member(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_SUSPENDED = "suspended"
    STATUS_INACTIVE = "inactive"
    STATUS_EXITED = "exited"

    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_SUSPENDED, "Suspended"),
        (STATUS_INACTIVE, "Inactive"),
        (STATUS_EXITED, "Exited"),
    ]

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    member_no = models.CharField(max_length=20, unique=True)
    id_number = models.CharField(max_length=50, unique=True)
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    date_joined = models.DateField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_INACTIVE
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="member",
    )

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.member_no})"

    @property
    def total_shares_amount(self):
        return self.shares.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    @property
    def total_deposits(self):
        return self.deposits.aggregate(total=Sum("amount"))["total"] or Decimal("0")


class Share(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="shares")
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    date = models.DateField(default=timezone.now)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.member} - {self.amount}"


class Deposit(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="deposits")
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    date = models.DateField(default=timezone.now)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.member} - {self.amount}"


class Loan(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_FULLY_PAID = "fully_paid"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_FULLY_PAID, "Fully Paid"),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="loans")
    amount_applied = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    amount_approved = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        validators=[MinValueValidator(0)],
    )
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0"),
        validators=[MinValueValidator(0)],
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    date_applied = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-date_applied"]

    def __str__(self):
        return f"{self.member} - {self.amount_applied} ({self.status})"

    @property
    def total_repaid(self):
        return (
            self.repayments.filter(status=LoanRepayment.STATUS_CONFIRMED)
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0")
        )

    @property
    def balance(self):
        return self.amount_approved - self.total_repaid


class LoanRepayment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
    ]

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="repayments")
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    date_paid = models.DateField(default=timezone.now)
    # Defaults to "pending" — repayments only count toward the loan balance
    # once staff explicitly confirm them. (Docs flagged the old default of
    # "confirmed" as an unresolved open question; this resolves it toward
    # the safer behavior. Revert to STATUS_CONFIRMED if that wasn't intended.)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )

    class Meta:
        ordering = ["-date_paid"]

    def __str__(self):
        return f"{self.loan} - {self.amount} ({self.status})"