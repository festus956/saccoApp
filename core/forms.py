from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Member

User = get_user_model()


def generate_member_no():
    """
    Generate the next sequential member_no.

    v1 approach: look at existing numeric member_no values and increment the
    highest one. Assumes member_no values are numeric strings (matches the
    existing data: "1", "2", ...). Revisit if member_no ever needs a
    non-numeric or staff-assigned scheme instead of self-service generation.
    """
    existing = Member.objects.values_list("member_no", flat=True)
    max_no = 0
    for no in existing:
        try:
            max_no = max(max_no, int(no))
        except (TypeError, ValueError):
            continue
    return str(max_no + 1)


class MemberRegistrationForm(UserCreationForm):
    """
    Self-service registration.

    Creates a User (is_active=False) and a linked Member (status="inactive").
    Django's auth backend already refuses to authenticate an inactive User,
    so no extra guard is needed to block login until staff approves — staff
    approval means flipping both User.is_active and Member.status via admin.
    """

    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    id_number = forms.CharField(max_length=50, required=True)
    phone_number = forms.CharField(max_length=20, required=True)
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def clean_id_number(self):
        id_number = self.cleaned_data["id_number"]
        if Member.objects.filter(id_number=id_number).exists():
            raise forms.ValidationError("A member with this ID number already exists.")
        return id_number

    def clean_phone_number(self):
        phone_number = self.cleaned_data["phone_number"]
        if Member.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError("A member with this phone number already exists.")
        return phone_number

    def clean_email(self):
        email = self.cleaned_data["email"]
        if Member.objects.filter(email=email).exists():
            raise forms.ValidationError("A member with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        # Pending staff approval — inactive until reviewed in the admin.
        user.is_active = False

        if commit:
            user.save()
            Member.objects.create(
                user=user,
                first_name=self.cleaned_data["first_name"],
                last_name=self.cleaned_data["last_name"],
                id_number=self.cleaned_data["id_number"],
                phone_number=self.cleaned_data["phone_number"],
                email=self.cleaned_data["email"],
                member_no=generate_member_no(),
                status="inactive",
            )
        return user