from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static





urlpatterns = [
    # ---------------------------
    # Admin
    # ---------------------------
    path("admin/", admin.site.urls),

    # ---------------------------
    # Home (simple landing/dashboard placeholder)
    # ---------------------------
    path("", TemplateView.as_view(template_name="home.html"), name="home",),
    # ---------------------------
    # Authentication / Accounts
    # ---------------------------
    path("accounts/", include("accounts.urls", namespace="accounts")),

    # ---------------------------
    # Budget app 
    # ---------------------------
    path("budget/", include("budget.urls", namespace="budget")),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
