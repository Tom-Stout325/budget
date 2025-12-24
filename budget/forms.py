from django import forms
from django.core.validators import FileExtensionValidator

from .models import Account, Bank


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





class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ["bank", "name", "account_type", "last4", "currency", "mapping_override", "is_active"]
        widgets = {
            "bank": forms.Select(attrs={"class": "form-select"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Chase Checking"}),
            "account_type": forms.Select(attrs={"class": "form-select"}),
            "last4": forms.TextInput(attrs={"class": "form-control", "placeholder": "optional"}),
            "currency": forms.TextInput(attrs={"class": "form-control", "placeholder": "USD"}),
            "mapping_override": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        
        
        
        



class BankForm(forms.ModelForm):
    class Meta:
        model = Bank
        fields = ["name", "mapping", "mapping_version", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Chase"}),
            "mapping": forms.Textarea(attrs={"class": "form-control", "rows": 8}),
            "mapping_version": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_name(self):
        return (self.cleaned_data["name"] or "").strip()
