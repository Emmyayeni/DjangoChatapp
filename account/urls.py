from django.urls import path 

from account.views import (
    account_view,
    edit_account,
    crop_image,
    test
)

app_name = "account"

urlpatterns = [
    path('<user_id>',account_view,name='view'),
    path('',test,name='view'),
    path('<user_id>/edit',edit_account,name='edit'),
    path('<user_id>/edit/cropImage',crop_image,name='crop_image'),
]
