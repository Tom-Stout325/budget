import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple

from django.db import transaction as db_transaction

from .models import Account, BankStatement, Transaction


COMMON_DATE = ["date", "posting date", "transaction date", "posted date"]
COMMON_DESC = ["description", "details", "memo", "merchant", "transaction description", "name"]
COMMON_AMOUNT = ["amount", "transaction amount"]
COMMON_DEBIT = ["debit", "withdrawal", "outflow", "charge"]
COMMON_CREDIT = ["credit", "deposit", "inflow", "payment"]
COMMON_BALANCE = ["balance", "running balance"]


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def _pick(headers: List[str], candidates: List[str]) -> Optional[str]:
    norm_map = {_norm(h): h for h in headers}
    for c in candidates:
        if c in norm_map:
            return norm_map[c]
    return None


def infer_mapping(headers: List[str]) -> Dict:
    """
    Minimal auto-detect mapping. If it can't find essentials, caller must prompt user later.
    """
    date_col = _pick(headers, COMMON_DATE)
    desc_col = _pick(headers, COMMON_DESC)
    amt_col = _pick(headers, COMMON_AMOUNT)
    debit_col = _pick(headers, COMMON_DEBIT)
    credit_col = _pick(headers, COMMON_CREDIT)
    bal_col = _pick(headers, COMMON_BALANCE)

    mapping: Dict = {
        "date_column": date_col,
        "description_column": desc_col,
        "balance_column": bal_col,
        # Prefer amount column if present, else debit/credit pair
        "amount_column": amt_col,
        "debit_column": debit_col if not amt_col else None,
        "credit_column": credit_col if not amt_col else None,
        # Common default; can be overridden per bank
        "date_format": None,
        "delimiter": ",",
        "skip_rows": 0,
    }
    return mapping


def parse_amount(value: str) -> Optional[Decimal]:
    """
    Robust amount parsing:
    - $1,234.56
    - (123.45)
    - -123.45
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None

    # handle parentheses as negative
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()

    s = s.replace("$", "").replace(",", "").replace(" ", "")
    try:
        amt = Decimal(s)
    except (InvalidOperation, ValueError):
        return None

    return -amt if negative else amt


def parse_date(value: str, date_format: Optional[str] = None):
    s = (value or "").strip()
    if not s:
        return None

    if date_format:
        try:
            return datetime.strptime(s, date_format).date()
        except ValueError:
            return None

    # try a few common formats
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue

    return None


def import_statement_csv(statement: BankStatement) -> Tuple[int, List[str]]:
    """
    Parses a CSV BankStatement into normalized Transaction rows.
    Returns (created_count, errors).
    """
    account: Account = statement.account
    effective_mapping = account.effective_mapping()

    errors: List[str] = []

    delimiter = effective_mapping.get("delimiter") or ","
    skip_rows = int(effective_mapping.get("skip_rows") or 0)
    date_format = effective_mapping.get("date_format")

    # Open uploaded file as text
    statement.source_file.open("rb")
    try:
        text = io.TextIOWrapper(statement.source_file.file, encoding="utf-8-sig", newline="")
        # Skip any pre-header rows if needed
        for _ in range(skip_rows):
            next(text, None)

        reader = csv.DictReader(text, delimiter=delimiter)
        headers = reader.fieldnames or []
        if not headers:
            return 0, ["CSV appears to have no header row."]

        # If mapping is missing essentials, try infer
        if not effective_mapping.get("date_column") or not effective_mapping.get("description_column"):
            inferred = infer_mapping(headers)
            # Merge inferred into effective mapping (keep explicit config if present)
            merged = {**inferred, **effective_mapping}
            effective_mapping = merged

        date_col = effective_mapping.get("date_column")
        desc_col = effective_mapping.get("description_column")
        amt_col = effective_mapping.get("amount_column")
        debit_col = effective_mapping.get("debit_column")
        credit_col = effective_mapping.get("credit_column")
        bal_col = effective_mapping.get("balance_column")
        ref_col = effective_mapping.get("reference_column")  # optional

        if not date_col or not desc_col:
            return 0, ["Missing required mapping: date_column and description_column."]

        if not amt_col and not (debit_col or credit_col):
            return 0, ["Missing required mapping: amount_column OR debit/credit columns."]

        txns_to_create: List[Transaction] = []
        row_count = 0
        bad_rows = 0

        for row in reader:
            row_count += 1

            dt = parse_date(row.get(date_col, ""), date_format=date_format)
            if not dt:
                bad_rows += 1
                continue

            desc = (row.get(desc_col) or "").strip()
            if not desc:
                desc = "(no description)"

            amount: Optional[Decimal] = None

            if amt_col:
                amount = parse_amount(row.get(amt_col, ""))
            else:
                # If both debit and credit exist, debit = expense (negative), credit = income (positive)
                debit = parse_amount(row.get(debit_col, "")) if debit_col else None
                credit = parse_amount(row.get(credit_col, "")) if credit_col else None

                if debit and debit != Decimal("0"):
                    amount = -abs(debit)
                elif credit and credit != Decimal("0"):
                    amount = abs(credit)

            if amount is None:
                bad_rows += 1
                continue

            balance = parse_amount(row.get(bal_col, "")) if bal_col else None
            raw_ref = (row.get(ref_col) or "").strip() if ref_col else ""

            txns_to_create.append(
                Transaction(
                    user=statement.user,
                    account=account,
                    statement=statement,
                    transaction_date=dt,
                    description=desc[:500],
                    amount=amount,
                    balance=balance,
                    raw_reference=raw_ref[:120],
                )
            )

        if bad_rows:
            errors.append(f"Skipped {bad_rows} row(s) due to missing/invalid date or amount.")

        # Save transactions
        with db_transaction.atomic():
            Transaction.objects.bulk_create(txns_to_create, batch_size=1000)

        # Update statement stats
        statement.row_count = row_count
        statement.mapping_version_used = account.bank.mapping_version
        statement.parsed_ok = True
        statement.parse_error = ""
        statement.save(update_fields=["row_count", "mapping_version_used", "parsed_ok", "parse_error"])

        return len(txns_to_create), errors

    finally:
        statement.source_file.close()
