from django.conf import settings
from django.db import models


class Bank(models.Model):
    """
    Represents a financial institution and its default CSV mapping.
    Mapping is stored as JSON so we can flex across different CSV schemas.
    """
    name = models.CharField(max_length=120, unique=True)
    mapping = models.JSONField(blank=True, null=True)  # default CSV mapping rules
    mapping_version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Account(models.Model):
    """
    A user's account (checking/savings/credit) that statements belong to.
    Accounts can optionally override the Bank's default mapping.
    """

    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT = "credit"
    CASH = "cash"
    OTHER = "other"

    ACCOUNT_TYPE_CHOICES = [
        (CHECKING, "Checking"),
        (SAVINGS, "Savings"),
        (CREDIT, "Credit Card"),
        (CASH, "Cash"),
        (OTHER, "Other"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="accounts")
    bank = models.ForeignKey(Bank, on_delete=models.PROTECT, related_name="accounts")
    name = models.CharField(max_length=120)  # "Chase Checking", "Apple Card"
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, default=CHECKING)

    # Optional: helps users distinguish accounts without storing sensitive numbers
    last4 = models.CharField(max_length=4, blank=True)
    currency = models.CharField(max_length=3, default="USD")

    # Optional overrides for slightly different exports per account
    mapping_override = models.JSONField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["user", "bank", "name"], name="uniq_account_user_bank_name")
        ]

    def __str__(self) -> str:
        return f"{self.name}"

    def effective_mapping(self) -> dict:
        """
        Bank mapping + account override mapping (override wins).
        Safe default to {} when missing.
        """
        base = self.bank.mapping or {}
        override = self.mapping_override or {}
        return {**base, **override}


def statement_upload_to(instance: "BankStatement", filename: str) -> str:
    # e.g. statements/user_5/account_12/2025-12-23_filename.csv
    # Keep it simple and organized.
    return f"statements/user_{instance.user_id}/account_{instance.account_id}/{filename}"


class BankStatement(models.Model):
    """
    One uploaded statement file (CSV or PDF). CSVs will be parsed into Transactions.
    PDFs are stored for reference unless you add parsing later.
    """

    SOURCE_CSV = "csv"
    SOURCE_PDF = "pdf"
    SOURCE_TYPE_CHOICES = [
        (SOURCE_CSV, "CSV"),
        (SOURCE_PDF, "PDF"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="statements")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="statements")

    source_file = models.FileField(upload_to=statement_upload_to)
    source_type = models.CharField(max_length=8, choices=SOURCE_TYPE_CHOICES, default=SOURCE_CSV)

    file_hash = models.CharField(max_length=64, db_index=True)  # sha256 hex
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Optional metadata you can fill during/after import
    statement_start_date = models.DateField(blank=True, null=True)
    statement_end_date = models.DateField(blank=True, null=True)
    row_count = models.PositiveIntegerField(default=0)

    # Save which mapping version was used when parsing (future-proof)
    mapping_version_used = models.PositiveIntegerField(default=1)

    # Parse status (for future preview/import step)
    parsed_ok = models.BooleanField(default=False)
    parse_error = models.TextField(blank=True)

    class Meta:
        ordering = ["-uploaded_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "account", "file_hash"], name="uniq_statement_user_account_hash")
        ]

    def __str__(self) -> str:
        return f"{self.account.name} ({self.uploaded_at:%Y-%m-%d})"


class Transaction(models.Model):
    """
    Normalized transaction row, used for all reporting.
    This is what your dashboard and PDFs will query.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="transactions")
    statement = models.ForeignKey(BankStatement, on_delete=models.CASCADE, related_name="transactions")

    transaction_date = models.DateField()
    description = models.CharField(max_length=500)

    # Signed amount: +income, -expense (normalizes across banks)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Optional
    balance = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    raw_reference = models.CharField(max_length=120, blank=True)  # bank-provided ID if present

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-transaction_date", "-id"]
        indexes = [
            models.Index(fields=["user", "transaction_date"]),
            models.Index(fields=["account", "transaction_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.transaction_date} {self.description[:40]} {self.amount}"
