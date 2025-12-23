import hashlib

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator

from formtools.wizard.views import SessionWizardView

from .forms import ImportSelectAccountForm, ImportUploadStatementForm
from .models import BankStatement  # we’ll create this next


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

    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if step == "account":
            kwargs["user"] = self.request.user
        return kwargs

    def _hash_uploaded_file(self, f) -> str:
        """
        Hash file contents for statement-level dedupe.
        Avoids loading entire file into memory at once.
        """
        h = hashlib.sha256()
        for chunk in f.chunks():
            h.update(chunk)
        return h.hexdigest()

    def done(self, form_list, **kwargs):
        form_data = {name: form.cleaned_data for name, form in zip(self.get_form_list().keys(), form_list)}
        account = form_data["account"]["account"]
        upload = form_data["upload"]["source_file"]

        file_hash = self._hash_uploaded_file(upload)
        ext = (upload.name.rsplit(".", 1)[-1] or "").lower()
        source_type = "pdf" if ext == "pdf" else "csv"

        # Dedupe: user + account + file_hash
        existing = BankStatement.objects.filter(
            user=self.request.user,
            account=account,
            file_hash=file_hash,
        ).first()

        if existing:
            messages.warning(
                self.request,
                f"This statement appears to be a duplicate (uploaded {existing.uploaded_at:%Y-%m-%d}).",
            )
            # For MVP: send them to a statement detail later; for now go home.
            return redirect("home")

        # Create statement record (we’ll parse CSV later)
        stmt = BankStatement.objects.create(
            user=self.request.user,
            account=account,
            source_file=upload,
            source_type=source_type,
            file_hash=file_hash,
            uploaded_at=timezone.now(),
        )

        if source_type == "pdf":
            messages.success(self.request, "PDF statement saved for reference. Upload a CSV to import transactions.")
            return redirect("home")

        messages.success(self.request, "Statement uploaded. Next we’ll add mapping + preview + import.")
        return redirect("home")
