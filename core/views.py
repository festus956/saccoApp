from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render

from .forms import MemberRegistrationForm
from .models import Loan, Member

# Create your views here.

# --------------------------------------------
# Auth
# --------------------------------------------


def loginpage(request):
    """
    Single login view for both members and staff.

    After authentication, redirects by role:
      - staff (User.is_staff=True) -> accounts' staff balance page
      - everyone else              -> core home

    Note: redirect("accounts:member_balance") resolves a namespaced URL name defined in
    accounts.urls (app_name = "accounts") this is a URL reverse lookup, not a Python import of
    anything in accounts, so it does not violate the "core never imports
    accounts" rule.
    """
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return _redirect_by_role(user)
        messages.error(request, "Invalid username or password.")

    return render(request, "core/login.html", {"form": form})


def _redirect_by_role(user):
    if user.is_staff:
        return redirect("accounts:member_balance")
    return redirect("home")


def logout_view(request):
    auth_logout(request)
    return redirect("loginpage")


def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = MemberRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Registration received. Your account will be reviewed by "
                "staff before you can log in.",
            )
            return redirect("loginpage")
    else:
        form = MemberRegistrationForm()

    return render(request, "core/register.html", {"form": form})


# --------------------------------------------
# Member-facing pages
# --------------------------------------------


@login_required
def home(request):
    member = Member.objects.filter(user=request.user).first()

    if member is None:
        # Logged-in user with no linked Member record (e.g. a staff-only
        # account visiting a member page directly). Nothing member-specific
        # to show — render the page in an empty state rather than erroring.
        messages.info(request, "No member profile is linked to this account.")
        return render(request, "core/home.html", {"member": None})

    context = {
        "member": member,
        "total_shares_amount": member.total_shares_amount,
        "total_deposits": member.total_deposits,
    }
    return render(request, "core/home.html", context)


@login_required
def loans(request):
    """
    Read-only for now: shows the member's own loan history and status.
    Application/submission is a separate, later piece of work.
    """
    member = Member.objects.filter(user=request.user).first()

    if member is None:
        messages.info(request, "No member profile is linked to this account.")
        return render(request, "core/loans.html", {"loans": []})

    member_loans = Loan.objects.filter(member=member).order_by("-id")
    return render(request, "core/loans.html", {"loans": member_loans})