from django import forms
from django.core.validators import FileExtensionValidator

from .models import Account  # we’ll create this next


class ImportSelectAccountForm(forms.Form):
    account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        empty_label="Select an account",
        widget=forms.Select(attrs={"class": "form-select"}),
        required=True,
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["account"].queryset = Account.objects.filter(user=user, is_active=True)


class ImportUploadStatementForm(forms.Form):
    source_file = forms.FileField(
        required=True,
        validators=[FileExtensionValidator(allowed_extensions=["csv", "pdf"])],
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
        help_text="Upload a CSV (recommended) or PDF (stored for reference).",
    )
