from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from core.models import Member

from .forms import MemberBalanceForm
from .models import MemberBalance
from .serializers import MemberBalanceSerializer

# Create your views here.

# --------------------------------------------
# Page Rendering
# --------------------------------------------


@login_required
def member_balance(request):
    context = {"form": MemberBalanceForm()}
    return render(request, "accounts/member_balance.html", context)


# --------------------------------------------
# API Endpoints
# --------------------------------------------


@api_view(["POST", "PUT"])
@permission_classes([IsAdminUser])
def member_balance_post(request):
    """
    Create or update a member's balance record.
    Staff-only: modifies core financial figures.
    """
    data = request.data
    member_uid = data.get("member_uid")
    if not member_uid:
        return Response(
            {"status": "error", "message": "Member UID is required."}, status=400
        )

    try:
        member = Member.objects.get(member_no=member_uid)
    except Member.DoesNotExist:
        return Response(
            {"status": "error", "message": "Member not found."}, status=404
        )

    instance = MemberBalance.objects.filter(member=member).first()

    if instance:
        serializer = MemberBalanceSerializer(instance, data=data, partial=True)
        success_message = "Member balance updated successfully."
        success_status = 200
    else:

        payload = data.copy()
        payload["member"] = member.pk
        serializer = MemberBalanceSerializer(data=payload)
        success_message = "Member balance created successfully."
        success_status = 201

    if not serializer.is_valid():
        return Response(
            {"status": "error", "message": "Invalid data.", "errors": serializer.errors},
            status=400,
        )

    serializer.save(member=member)

    return Response(
        {"status": "success", "message": success_message, "data": serializer.data},
        status=success_status,
    )


@api_view(["GET"])
@permission_classes([IsAdminUser])
def member_balance_actions(request, member_uid):
    """
    Retrieve a member's balance by member UID (member_no).
    """
    member_balance_obj = MemberBalance.objects.filter(member__member_no=member_uid).first()
    if not member_balance_obj:
        return Response(
            {"status": "error", "message": "Member balance not found."}, status=404
        )

    member = member_balance_obj.member
    data = MemberBalanceSerializer(member_balance_obj).data
    data["member"] = {
        "uid": member.member_no,
        "fullname": f"{member.first_name} {member.last_name}",
    }
    data["max_loan_amount"] = member_balance_obj.get_a_member_summary()["max_loan_amount"]

    return Response(
        {"status": "success", "message": "Member balance retrieved successfully.", "data": data},
        status=200,
    )