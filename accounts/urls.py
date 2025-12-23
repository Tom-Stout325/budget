# accounts/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = "accounts"

urlpatterns = [
    # -----------------------------
    # Auth: Login / Logout
    # -----------------------------
    path("login/", auth_views.LoginView.as_view( template_name="accounts/login.html",redirect_authenticated_user=True,), name="login",),
    path("logout/", auth_views.LogoutView.as_view(), name="logout",),

    # -----------------------------
    # Auth: Password reset flow
    # -----------------------------
    path("password-reset/", auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.html",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url="done/",), name="password_reset",),
    path("password-reset/done/",auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html",),name="password_reset_done",),
    path("reset/<uidb64>/<token>/",auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url="/accounts/reset/done/",),name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html",), name="password_reset_complete",),

    # -----------------------------
    # Auth: Password change (logged-in)
    # -----------------------------
    path("password-change/", auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change_form.html",
            success_url="/accounts/password-change/done/",), name="password_change",),
    path("password-change/done/", auth_views.PasswordChangeDoneView.as_view(
            template_name="accounts/password_change_done.html",), name="password_change_done",),

    # -----------------------------
    # Registration (your custom view)
    # -----------------------------
    path("register/", views.register, name="register"),
]
