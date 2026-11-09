"""Strict CSV normalization for bank and ledger exports.

Accepted dates: YYYY-MM-DD and DD/MM/YYYY. Amounts are represented in integer
minor units (paise/cents); debit is negative and credit is positive.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


MAX_CSV_BYTES = 5 * 1024 * 1024
MAX_ROWS = 10_000


@dataclass(frozen=True)
class ImportedRow:
    source_row_number: int
    transaction_date: date
    description: str
    reference: str
    amount_minor: int
    currency: str


def _first(row: dict, *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return ""


def _parse_date(value: str) -> date:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError("date must be YYYY-MM-DD or DD/MM/YYYY")


def _minor_units(value: str) -> int:
    try:
        amount = Decimal(value.replace(",", "").strip())
    except (InvalidOperation, AttributeError):
        raise ValueError("amount must be a valid decimal number")
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def parse_csv_content(content: str, *, max_rows: int = MAX_ROWS) -> list[ImportedRow]:
    if not isinstance(content, str) or not content.strip():
        raise ValueError("CSV content is empty")
    if len(content.encode("utf-8")) > MAX_CSV_BYTES:
        raise ValueError(f"CSV exceeds {MAX_CSV_BYTES} byte limit")

    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise ValueError("CSV header row is required")
    headers = {str(h).strip().lower() for h in reader.fieldnames if h}
    if not ({"transaction_date", "posting_date", "date"} & headers):
        raise ValueError("missing date column: transaction_date, posting_date or date")
    if not ({"amount"} <= headers or ({"debit"} <= headers and {"credit"} <= headers)):
        raise ValueError("provide amount, or both debit and credit columns")

    rows: list[ImportedRow] = []
    for line_number, raw in enumerate(reader, start=2):
        if line_number > max_rows + 1:
            raise ValueError(f"CSV exceeds {max_rows} data-row limit")
        if None in raw:
            raise ValueError(f"row {line_number}: extra columns detected")
        row = {str(k).strip().lower(): (v or "").strip() for k, v in raw.items() if k}
        if not any(row.values()):
            continue
        try:
            date_value = _first(row, "transaction_date", "posting_date", "date")
            txn_date = _parse_date(date_value)
            amount_value = _first(row, "amount")
            if amount_value:
                amount_minor = _minor_units(amount_value)
            else:
                credit = _minor_units(_first(row, "credit") or "0")
                debit = _minor_units(_first(row, "debit") or "0")
                amount_minor = credit - debit
            currency = (_first(row, "currency") or "INR").upper()
            if len(currency) != 3 or not currency.isalpha():
                raise ValueError("currency must be a three-letter code")
            rows.append(ImportedRow(
                source_row_number=line_number,
                transaction_date=txn_date,
                description=_first(row, "description", "narration", "details"),
                reference=_first(row, "reference", "utr", "transaction_id", "ref"),
                amount_minor=amount_minor,
                currency=currency,
            ))
        except ValueError as exc:
            raise ValueError(f"row {line_number}: {exc}") from exc
    if not rows:
        raise ValueError("CSV contains no transaction rows")
    return rows
