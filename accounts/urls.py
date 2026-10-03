from django.urls import path

from .views import member_balance, member_balance_actions, member_balance_post



from django.urls import path
from .views import member_balance, member_balance_actions, member_balance_post

app_name = "accounts"

urlpatterns = [
    path("member-balance/", member_balance, name="member_balance"),
    path("balances/", member_balance_post, name="member_balance_save"),
    path("balances/<str:member_uid>/", member_balance_actions, name="member_balance_by_uid"),

]