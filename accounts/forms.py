
from django import forms

from .models import MemberBalance


class MemberBalanceForm(forms.ModelForm):
    class Meta:
        model = MemberBalance
        fields = [
            "member",
            "share",
            "deposits",
            "loans_balance",
            "wd_account",
            "date_imported",
            "shares_balance_imported",
            "deposits_balance_imported",
            "is_active",
            "is_deleted",
        ]
        widgets = {
            "member": forms.Select(attrs={"class": "form-control"}),
            "share": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "deposits": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "loans_balance": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "wd_account": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "date_imported": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "shares_balance_imported": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "deposits_balance_imported": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_deleted": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_share(self):
        value = self.cleaned_data["share"]
        if value < 0:
            raise forms.ValidationError("Share balance cannot be negative.")
        return value

    def clean_deposits(self):
        value = self.cleaned_data["deposits"]
        if value < 0:
            raise forms.ValidationError("Deposits balance cannot be negative.")
        return value

    def clean_loans_balance(self):
        value = self.cleaned_data["loans_balance"]
        if value < 0:
            raise forms.ValidationError("Loan balance cannot be negative.")
        return value
    def clean_wd_account(self):
        value = self.cleaned_data["wd_account"]
        if value < 0:
            raise forms.ValidationError("Withdrawal account balance cannot be negative.")
        return value
