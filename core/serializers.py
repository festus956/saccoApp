from rest_framework import serializers

from .models import Deposit, Loan, LoanRepayment, Member, Share


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = [
            "id",
            "first_name",
            "last_name",
            "member_no",
            "id_number",
            "phone_number",
            "email",
            "date_joined",
            "status",
            "total_shares_amount",
            "total_deposits",
        ]
        read_only_fields = ["id", "date_joined", "total_shares_amount", "total_deposits"]


class ShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = Share
        fields = ["id", "member", "amount", "date"]
        read_only_fields = ["id"]

    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Share amount cannot be negative.")
        return value


class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = ["id", "member", "amount", "date"]
        read_only_fields = ["id"]

    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Deposit amount cannot be negative.")
        return value


class LoanSerializer(serializers.ModelSerializer):
    total_repaid = serializers.ReadOnlyField()
    balance = serializers.ReadOnlyField()

    class Meta:
        model = Loan
        fields = [
            "id",
            "member",
            "amount_applied",
            "amount_approved",
            "interest_rate",
            "status",
            "date_applied",
            "total_repaid",
            "balance",
        ]
        read_only_fields = ["id", "date_applied", "total_repaid", "balance"]

    def validate_amount_applied(self, value):
        if value < 0:
            raise serializers.ValidationError("Amount applied cannot be negative.")
        return value

    def validate_amount_approved(self, value):
        if value < 0:
            raise serializers.ValidationError("Amount approved cannot be negative.")
        return value


class LoanRepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanRepayment
        fields = ["id", "loan", "amount", "date_paid", "status"]
        read_only_fields = ["id"]

    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Repayment amount cannot be negative.")
        return value