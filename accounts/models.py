from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum

from core.models import Member

# Create your models here.


class MemberBalance(models.Model):


    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name="balance")

    # Live balances
    share = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    deposits = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    loans_balance = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    wd_account = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )

    # Legacy import snapshot (from previous system, at cutover)
    date_imported = models.DateTimeField(
        null=True, blank=True,
        help_text="Date the balance was imported from the previous system.",
    )
    shares_balance_imported = models.IntegerField(
        default=0, help_text="Legacy share count at time of import (not a currency amount)."
    )
    deposits_balance_imported = models.IntegerField(
        default=0, help_text="Legacy deposits count at time of import (not a currency amount)."
    )

    date_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.member.first_name} {self.member.last_name} - {self.share} - {self.deposits}"

    class Meta:
        verbose_name = "Member Balance"
        verbose_name_plural = "Member Balances"
        db_table = "member_balance"
        ordering = ["member__first_name"]

    def get_a_member_summary(self):
        multiplier = getattr(settings, "LOAN_MULTIPLIER", 3)
        return {
            "member": self.member.member_no,
            "share": self.share,
            "deposits": self.deposits,
            "loans": self.loans_balance,
            "wd_account": self.wd_account,
            "max_loan_amount": self.deposits * multiplier,
            "loan_eligibility": self.deposits * multiplier - self.loans_balance,
        }

    @classmethod
    def get_sacco_stats(cls):
        queryset = cls.objects.filter(is_active=True, is_deleted=False)
        totals = queryset.aggregate(
            total_deposits=Sum("deposits"),
            total_loans=Sum("loans_balance"),
            total_shares=Sum("share"),
        )
        total_deposits = totals["total_deposits"] or 0
        total_loans = totals["total_loans"] or 0
        return {
            "total_members": queryset.count(),
            "total_deposits": total_deposits,
            "total_loans": total_loans,
            "total_shares": totals["total_shares"] or 0,
            "loans_over_deposits": (total_loans / total_deposits) if total_deposits else 0,
        }