from django.urls import path
from django.views.generic import TemplateView

from .views_accounts import AccountCreateView

from .views import (
        StatementImportWizard,
        BankListView,
        BankCreateView,
        BankUpdateView,
)


app_name = "budget"

urlpatterns = [
    path("import/", StatementImportWizard.as_view(), name="import_statement"),
    
    # Accounts
    path("accounts/new/", AccountCreateView.as_view(), name="account_create"),

    # Placeholders for navbar dropdown (so nothing 404s)
    path("", TemplateView.as_view(template_name="budget/dashboard.html"), name="dashboard"),
    path("reports/", TemplateView.as_view(template_name="budget/reports.html"), name="reports"),
    path("pdfs/", TemplateView.as_view(template_name="budget/pdfs.html"), name="pdfs"),
    path("upload/", StatementImportWizard.as_view(), name="upload_csv"),
    
    path("banks/", BankListView.as_view(), name="bank_list"),
    path("banks/new/", BankCreateView.as_view(), name="bank_create"),
    path("banks/<int:pk>/edit/", BankUpdateView.as_view(), name="bank_edit"),
]
