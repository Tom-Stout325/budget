from django.urls import path
from .views import StatementImportWizard

app_name = "budget"

urlpatterns = [
    path("import/", StatementImportWizard.as_view(), name="import_statement"),
]
