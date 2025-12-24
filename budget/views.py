import hashlib

from django.contrib import messages
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView, UpdateView

from formtools.wizard.views import SessionWizardView

from .importers import import_statement_csv

from .forms import (
        ImportSelectAccountForm, 
        ImportUploadStatementForm, 
        BankForm
)
from .models import (
        BankStatement, 
        Bank,
)







FORMS = [
    ("account", ImportSelectAccountForm),
    ("upload", ImportUploadStatementForm),
]

TEMPLATES = {
    "account": "budget/import/account_step.html",
    "upload": "budget/import/upload_step.html",
}




@method_decorator(login_required, name="dispatch")
class StatementImportWizard(SessionWizardView):
    form_list = FORMS

    # REQUIRED for file uploads in a wizard
    file_storage = FileSystemStorage(location=settings.MEDIA_ROOT)

    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if step == "account":
            kwargs["user"] = self.request.user
        return kwargs

    # ✅ PUT THE METHOD RIGHT HERE
    def _hash_uploaded_file(self, f) -> str:
        h = hashlib.sha256()
        for chunk in f.chunks():
            h.update(chunk)
        # rewind so Django can save it later
        try:
            f.seek(0)
        except Exception:
            pass
        return h.hexdigest()

    def done(self, form_list, **kwargs):
        form_data = {
            name: form.cleaned_data
            for name, form in zip(self.get_form_list().keys(), form_list)
        }

        account = form_data["account"]["account"]
        upload = form_data["upload"]["source_file"]

        file_hash = self._hash_uploaded_file(upload)
        ext = upload.name.rsplit(".", 1)[-1].lower()
        source_type = "pdf" if ext == "pdf" else "csv"

        stmt = BankStatement.objects.create(
            user=self.request.user,
            account=account,
            source_file=upload,
            source_type=source_type,
            file_hash=file_hash,
        )

        if source_type == "pdf":
            messages.success(self.request, "PDF saved for reference.")
            return redirect("budget:dashboard")

        created_count, errors = import_statement_csv(stmt)

        if errors:
            for e in errors:
                messages.warning(self.request, e)

        messages.success(self.request, f"Imported {created_count} transaction(s).")
        return redirect("budget:dashboard")







class BankListView(LoginRequiredMixin, ListView):
    model = Bank
    template_name = "budget/banks/bank_list.html"
    context_object_name = "banks"
    paginate_by = 50

    def get_queryset(self):
        return Bank.objects.order_by("name")


class BankCreateView(LoginRequiredMixin, CreateView):
    model = Bank
    form_class = BankForm
    template_name = "budget/banks/bank_form.html"

    def get_success_url(self):
        return reverse("budget:bank_list")


class BankUpdateView(LoginRequiredMixin, UpdateView):
    model = Bank
    form_class = BankForm
    template_name = "budget/banks/bank_form.html"

    def get_success_url(self):
        return reverse("budget:bank_list")
