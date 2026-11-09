"""Pure-Python deterministic reconciliation primitives.

No database, Frappe or LLM dependency is required. Amounts are integer minor units
(e.g. paise/cents) to avoid floating-point currency arithmetic.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Iterable, Optional


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    amount_minor: int
    transaction_date: date
    reference: str = ""
    currency: str = "INR"
    description: str = ""


@dataclass(frozen=True)
class MatchCandidate:
    bank_transaction_id: str
    ledger_transaction_id: str
    rule: str
    confidence: str


def normalize_reference(value: str) -> str:
    """Normalize reference identifiers conservatively; do not remove digits."""
    return "".join(ch for ch in (value or "").upper() if ch.isalnum())


def find_exact_matches(
    bank_rows: Iterable[Transaction],
    ledger_rows: Iterable[Transaction],
    *,
    date_window_days: int = 0,
) -> list[MatchCandidate]:
    """Return unambiguous one-to-one candidates by amount/currency/reference/date.

    Rows with a non-unique candidate on either side are deliberately not matched.
    This starter implementation does not perform partial or many-to-many matching.
    """
    banks = list(bank_rows)
    ledgers = list(ledger_rows)
    ledger_index: dict[tuple[int, str, str], list[Transaction]] = defaultdict(list)
    bank_index: dict[tuple[int, str, str], list[Transaction]] = defaultdict(list)

    for row in ledgers:
        ref = normalize_reference(row.reference)
        if ref:
            ledger_index[(row.amount_minor, row.currency.upper(), ref)].append(row)
    for row in banks:
        ref = normalize_reference(row.reference)
        if ref:
            bank_index[(row.amount_minor, row.currency.upper(), ref)].append(row)

    candidates: list[MatchCandidate] = []
    for bank in banks:
        ref = normalize_reference(bank.reference)
        if not ref:
            continue
        key = (bank.amount_minor, bank.currency.upper(), ref)
        possible = ledger_index.get(key, [])
        if len(possible) != 1 or len(bank_index.get(key, [])) != 1:
            continue
        ledger = possible[0]
        if abs((bank.transaction_date - ledger.transaction_date).days) > date_window_days:
            continue
        candidates.append(MatchCandidate(
            bank_transaction_id=bank.transaction_id,
            ledger_transaction_id=ledger.transaction_id,
            rule="exact_amount_currency_reference_date_window",
            confidence="high",
        ))
    return candidates


def find_duplicate_fingerprints(rows: Iterable[Transaction]) -> dict[tuple, list[str]]:
    """Identify repeated normalized transaction fingerprints within one import."""
    groups: dict[tuple, list[str]] = defaultdict(list)
    for row in rows:
        key = (
            row.transaction_date.isoformat(),
            row.amount_minor,
            row.currency.upper(),
            normalize_reference(row.reference),
            (row.description or "").strip().casefold(),
        )
        groups[key].append(row.transaction_id)
    return {key: ids for key, ids in groups.items() if len(ids) > 1}
