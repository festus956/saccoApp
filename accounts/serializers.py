from rest_framework import serializers

from core.models import Member

from .models import MemberBalance


class MemberBalanceSerializer(serializers.ModelSerializer):
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects.all())
    member_no = serializers.CharField(source="member.member_no", read_only=True)
    member_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MemberBalance
        fields = [
            "id",
            "member",
            "member_no",
            "member_name",
            "share",
            "deposits",
            "loans_balance",
            "wd_account",
            "date_imported",
            "shares_balance_imported",
            "deposits_balance_imported",
            "date_updated",
            "is_active",
            "is_deleted",
        ]
        read_only_fields = ["id", "date_updated"]

    def get_member_name(self, obj):
        return f"{obj.member.first_name} {obj.member.last_name}"

    def validate_share(self, value):
        if value < 0:
            raise serializers.ValidationError("Share balance cannot be negative.")
        return value

    def validate_deposits(self, value):
        if value < 0:
            raise serializers.ValidationError("Deposits balance cannot be negative.")
        return value

    def validate_loans_balance(self, value):
        if value < 0:
            raise serializers.ValidationError("Loan balance cannot be negative.")
        return value
    def validate_wd_account(self, value):
        if value < 0:
            raise serializers.ValidationError("Withdrawal account balance cannot be negative.")
        return value