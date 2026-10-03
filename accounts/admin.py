
from django.contrib import admin

from .models import MemberBalance


@admin.register(MemberBalance)
class MemberBalanceAdmin(admin.ModelAdmin):
    list_display = (
        "member",
        "share",
        "deposits",
        "loans_balance",
        "wd_account",
        "is_active",
        "is_deleted",
        "date_updated",
    )
    list_filter = ("is_active", "is_deleted", "date_imported")
    search_fields = (
        "member__first_name",
        "member__last_name",
        "member__member_no",
        "member__id_number",
    )
    readonly_fields = ("date_updated",)
    ordering = ("member__first_name",)
    list_select_related = ("member",)

    fieldsets = (
        (None, {"fields": ("member",)}),
        ("Live Balances", {"fields": ("share", "deposits", "loans_balance", "wd_account")}),
        ("Legacy Import Snapshot", {"fields": ("date_imported", "shares_balance_imported", "deposits_balance_imported")}),
        ("Status", {"fields": ("is_active", "is_deleted", "date_updated")}),
    )
