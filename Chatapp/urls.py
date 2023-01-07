"""Chatapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path,include
from personal import views
from django.conf import settings
from django.conf.urls.static import static
from account.views import *
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.home_screen,name='home'),
    path('public_home',views.public_chat,name='public'),
    path('account/',include('account.urls'),name='account'),
    path('friend/',include('friend.urls'),name='friend'),
    path('chat/',include('chat.urls'),name='chat'),
    path('register',register_view,name='register'),
    path('login',Login,name='login'),
    path('logout',logout_view,name='logout'),
    path('account_search_results',account_search_results,name='account_search_results'),
    path('edit_account',edit_account,name='edit_account'),
    # password reset links 
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name="account/password_change_done.html"),name='password_change_done'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name="account/password_change.html"),name='password_change'),
    path('password_reset/done', auth_views.PasswordResetDoneView.as_view(template_name="account/password_reset_done.html"),name='password_reset_done'),
    path('reset/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view(),name='password_reset_confirm'),
    path('password_reset/', auth_views.PasswordResetView.as_view(),name='password_reset'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name="account/password_reset_complete.html"),name='password_reset_complete'),

]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
