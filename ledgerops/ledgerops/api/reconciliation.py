"""Deterministic bank-to-ledger reconciliation endpoint."""
from __future__ import annotations

from collections import defaultdict
from datetime import date

import frappe
from frappe import _

from ledgerops.ledgerops.services.reconciliation import (
    Transaction, find_duplicate_fingerprints, find_exact_matches, normalize_reference,
)


def _require_create(doctype: str) -> None:
    if not frappe.has_permission(doctype, ptype="create"):
        frappe.throw(_("You do not have permission to create {0}").format(doctype), frappe.PermissionError)


def _audit(action: str, doctype: str, name: str, details: str = "") -> None:
    frappe.get_doc({
        "doctype": "LedgerOps Audit Event",
        "actor": frappe.session.user,
        "action": action,
        "reference_doctype": doctype,
        "reference_name": name,
        "details": details[:2000],
    }).insert()


def _to_transaction(row) -> Transaction:
    return Transaction(
        transaction_id=row.name,
        amount_minor=int(row.amount_minor),
        transaction_date=date.fromisoformat(str(row.transaction_date)),
        reference=row.reference or "",
        currency=(row.currency or "INR").upper(),
        description=row.description or "",
    )


def _create_exception(client, batch, exception_type, title, description, bank_id=None, ledger_id=None):
    doc = frappe.get_doc({
        "doctype": "LedgerOps Exception",
        "client": client,
        "import_batch": batch,
        "bank_transaction": bank_id,
        "ledger_transaction": ledger_id,
        "exception_type": exception_type,
        "title": title[:140],
        "description": description[:2000],
        "status": "Open",
        "priority": "High" if exception_type in ("AMBIGUOUS_MATCH", "AMOUNT_DIFFERENCE", "DATE_DIFFERENCE") else "Medium",
    }).insert()
    return doc.name


@frappe.whitelist()
def reconcile(bank_batch: str, ledger_batch: str, date_window_days: int = 0):
    """Reconcile two imported batches; creates proposed matches and review exceptions.

    POST /api/method/ledgerops.ledgerops.api.reconciliation.reconcile
    Exact unique matches only: signed amount + currency + normalized reference
    + date window. No partial, many-to-many, FX or fuzzy matching.
    """
    try:
        window = int(date_window_days)
    except (TypeError, ValueError):
        frappe.throw(_("date_window_days must be an integer"))
    if window < 0 or window > 30:
        frappe.throw(_("date_window_days must be between 0 and 30"))

    for doctype in ("LedgerOps Match", "LedgerOps Exception", "LedgerOps Audit Event"):
        _require_create(doctype)

    bank_doc = frappe.get_doc("LedgerOps Import Batch", bank_batch)
    ledger_doc = frappe.get_doc("LedgerOps Import Batch", ledger_batch)
    bank_doc.check_permission("read")
    ledger_doc.check_permission("read")

    if bank_doc.source_type != "Bank Statement" or ledger_doc.source_type != "Ledger Export":
        frappe.throw(_("Provide a Bank Statement batch and a Ledger Export batch"))
    if bank_doc.client != ledger_doc.client:
        frappe.throw(_("Both batches must belong to the same client"))
    if bank_doc.status != "Imported" or ledger_doc.status != "Imported":
        frappe.throw(_("Both batches must be in Imported status; each batch can be reconciled once"))

    bank_rows = frappe.get_all(
        "LedgerOps Bank Transaction",
        filters={"import_batch": bank_batch},
        fields=["name", "amount_minor", "transaction_date", "reference", "currency", "description"],
        limit_page_length=10001,
    )
    ledger_rows = frappe.get_all(
        "LedgerOps Ledger Transaction",
        filters={"import_batch": ledger_batch},
        fields=["name", "amount_minor", "transaction_date", "reference", "currency", "description"],
        limit_page_length=10001,
    )
    if len(bank_rows) > 10000 or len(ledger_rows) > 10000:
        frappe.throw(_("Batch exceeds the 10,000-row synchronous reconciliation limit"))

    banks = [_to_transaction(row) for row in bank_rows]
    ledgers = [_to_transaction(row) for row in ledger_rows]
    candidates = find_exact_matches(banks, ledgers, date_window_days=window)
    matched_bank = {m.bank_transaction_id for m in candidates}
    matched_ledger = {m.ledger_transaction_id for m in candidates}

    for candidate in candidates:
        frappe.get_doc({
            "doctype": "LedgerOps Match",
            "bank_transaction": candidate.bank_transaction_id,
            "ledger_transaction": candidate.ledger_transaction_id,
            "rule": candidate.rule,
            "confidence": candidate.confidence,
            "status": "Proposed",
        }).insert()
        frappe.db.set_value("LedgerOps Bank Transaction", candidate.bank_transaction_id, "matched", 1)
        frappe.db.set_value("LedgerOps Ledger Transaction", candidate.ledger_transaction_id, "matched", 1)

    ledger_refs = defaultdict(list)
    bank_refs = defaultdict(list)
    for txn in ledgers:
        ref = normalize_reference(txn.reference)
        if ref:
            ledger_refs[ref].append(txn)
    for txn in banks:
        ref = normalize_reference(txn.reference)
        if ref:
            bank_refs[ref].append(txn)

    duplicate_bank = find_duplicate_fingerprints(banks)
    duplicate_ledger = find_duplicate_fingerprints(ledgers)
    duplicate_bank_ids = {name for ids in duplicate_bank.values() for name in ids}
    duplicate_ledger_ids = {name for ids in duplicate_ledger.values() for name in ids}
    handled_ledger_ids = set()
    exceptions_created = 0

    # Create one linked exception for a clear amount/date mismatch rather than
    # creating duplicate work items on both sides of the same discrepancy.
    for txn in banks:
        if txn.transaction_id in matched_bank:
            continue
        ref = normalize_reference(txn.reference)
        counterparts = ledger_refs.get(ref, []) if ref else []
        if txn.transaction_id in duplicate_bank_ids:
            kind, title = "DUPLICATE_BANK", "Possible duplicate bank transaction"
            ledger_id = None
        elif len(counterparts) > 1:
            kind, title = "AMBIGUOUS_MATCH", "Multiple ledger candidates"
            handled_ledger_ids.update(item.transaction_id for item in counterparts)
            ledger_id = None
        elif len(counterparts) == 1:
            other = counterparts[0]
            if other.transaction_id in matched_ledger:
                kind, title, ledger_id = "UNMATCHED_BANK", "No available ledger match", None
            elif other.currency == txn.currency and other.amount_minor != txn.amount_minor:
                kind, title, ledger_id = "AMOUNT_DIFFERENCE", "Bank and ledger amounts differ", other.transaction_id
                handled_ledger_ids.add(other.transaction_id)
            elif other.currency == txn.currency and other.amount_minor == txn.amount_minor and abs((other.transaction_date - txn.transaction_date).days) > window:
                kind, title, ledger_id = "DATE_DIFFERENCE", "Bank and ledger dates differ", other.transaction_id
                handled_ledger_ids.add(other.transaction_id)
            else:
                kind, title, ledger_id = "UNMATCHED_BANK", "No exact ledger match", None
        else:
            kind, title, ledger_id = "UNMATCHED_BANK", "No exact ledger match", None
        details = f"Bank row {txn.transaction_id}; date={txn.transaction_date}; amount_minor={txn.amount_minor}; currency={txn.currency}; reference={txn.reference}"
        if ledger_id:
            other = next(item for item in counterparts if item.transaction_id == ledger_id)
            details += f" | Ledger row {other.transaction_id}; date={other.transaction_date}; amount_minor={other.amount_minor}; currency={other.currency}"
        _create_exception(bank_doc.client, bank_batch, kind, title, details,
                          bank_id=txn.transaction_id, ledger_id=ledger_id)
        exceptions_created += 1

    for txn in ledgers:
        if txn.transaction_id in matched_ledger or txn.transaction_id in handled_ledger_ids:
            continue
        if txn.transaction_id in duplicate_ledger_ids:
            kind, title = "DUPLICATE_LEDGER", "Possible duplicate ledger transaction"
        else:
            ref = normalize_reference(txn.reference)
            counterparts = bank_refs.get(ref, []) if ref else []
            if len(counterparts) > 1:
                kind, title = "AMBIGUOUS_MATCH", "Multiple bank candidates"
            else:
                kind, title = "UNMATCHED_LEDGER", "No exact bank match"
        details = f"Ledger row {txn.transaction_id}; date={txn.transaction_date}; amount_minor={txn.amount_minor}; currency={txn.currency}; reference={txn.reference}"
        _create_exception(ledger_doc.client, ledger_batch, kind, title, details,
                          ledger_id=txn.transaction_id)
        exceptions_created += 1

    bank_doc.status = "Reconciled"
    bank_doc.save()
    ledger_doc.status = "Reconciled"
    ledger_doc.save()
    _audit("RECONCILIATION_COMPLETED", "LedgerOps Import Batch", bank_batch,
           f"ledger_batch={ledger_batch}; matches={len(candidates)}; exceptions={exceptions_created}; date_window_days={window}")

    return {
        "bank_batch": bank_batch,
        "ledger_batch": ledger_batch,
        "proposed_matches": len(candidates),
        "exceptions_created": exceptions_created,
        "date_window_days": window,
        "matching_rule": "unique exact signed amount + currency + normalized reference + date window",
    }
