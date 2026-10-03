
from django.contrib import admin

from .models import Member, Share, Deposit, Loan, LoanRepayment


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("member_no", "first_name", "last_name", "phone_number", "status", "date_joined")
    search_fields = ("first_name", "last_name", "member_no", "id_number", "phone_number", "email")
    list_filter = ("status",)


admin.site.register(Share)
admin.site.register(Deposit)
admin.site.register(Loan)
admin.site.register(LoanRepayment)
