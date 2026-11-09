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


def _create_exception(client, batch, txn, side, exception_type, title, description):
    bank_link = txn.transaction_id if side == "bank" else None
    ledger_link = txn.transaction_id if side == "ledger" else None
    doc = frappe.get_doc({
        "doctype": "LedgerOps Exception",
        "client": client,
        "import_batch": batch,
        "bank_transaction": bank_link,
        "ledger_transaction": ledger_link,
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
    Matches require a unique exact amount + currency + normalized reference
    within the date window. No partial, many-to-many, FX or fuzzy matching.
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

    created_matches = 0
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
        created_matches += 1

    bank_by_id = {t.transaction_id: t for t in banks}
    ledger_by_id = {t.transaction_id: t for t in ledgers}
    ledger_refs = defaultdict(list)
    bank_refs = defaultdict(list)
    for t in ledgers:
        ref = normalize_reference(t.reference)
        if ref:
            ledger_refs[ref].append(t)
    for t in banks:
        ref = normalize_reference(t.reference)
        if ref:
            bank_refs[ref].append(t)

    exception_count = 0
    duplicate_bank = find_duplicate_fingerprints(banks)
    duplicate_ledger = find_duplicate_fingerprints(ledgers)
    duplicate_bank_ids = {name for ids in duplicate_bank.values() for name in ids}
    duplicate_ledger_ids = {name for ids in duplicate_ledger.values() for name in ids}

    for txn in banks:
        if txn.transaction_id in matched_bank:
            continue
        if txn.transaction_id in duplicate_bank_ids:
            kind, title = "DUPLICATE_BANK", "Possible duplicate bank transaction"
        else:
            ref = normalize_reference(txn.reference)
            candidates_for_ref = ledger_refs.get(ref, []) if ref else []
            if len(candidates_for_ref) > 1:
                kind, title = "AMBIGUOUS_MATCH", "Multiple ledger candidates"
            elif candidates_for_ref and candidates_for_ref[0].currency == txn.currency and candidates_for_ref[0].amount_minor != txn.amount_minor:
                kind, title = "AMOUNT_DIFFERENCE", "Bank and ledger amounts differ"
            elif candidates_for_ref and candidates_for_ref[0].amount_minor == txn.amount_minor and abs((candidates_for_ref[0].transaction_date - txn.transaction_date).days) > window:
                kind, title = "DATE_DIFFERENCE", "Bank and ledger dates differ"
            else:
                kind, title = "UNMATCHED_BANK", "No exact ledger match"
        description = f"Bank row {txn.transaction_id}; date={txn.transaction_date}; amount_minor={txn.amount_minor}; currency={txn.currency}; reference={txn.reference}"
        _create_exception(bank_doc.client, bank_batch, txn, "bank", kind, title, description)
        exception_count += 1

    for txn in ledgers:
        if txn.transaction_id in matched_ledger:
            continue
        if txn.transaction_id in duplicate_ledger_ids:
            kind, title = "DUPLICATE_LEDGER", "Possible duplicate ledger transaction"
        else:
            ref = normalize_reference(txn.reference)
            candidates_for_ref = bank_refs.get(ref, []) if ref else []
            if len(candidates_for_ref) > 1:
                kind, title = "AMBIGUOUS_MATCH", "Multiple bank candidates"
            elif candidates_for_ref and candidates_for_ref[0].currency == txn.currency and candidates_for_ref[0].amount_minor != txn.amount_minor:
                kind, title = "AMOUNT_DIFFERENCE", "Ledger and bank amounts differ"
            elif candidates_for_ref and candidates_for_ref[0].amount_minor == txn.amount_minor and abs((candidates_for_ref[0].transaction_date - txn.transaction_date).days) > window:
                kind, title = "DATE_DIFFERENCE", "Ledger and bank dates differ"
            else:
                kind, title = "UNMATCHED_LEDGER", "No exact bank match"
        description = f"Ledger row {txn.transaction_id}; date={txn.transaction_date}; amount_minor={txn.amount_minor}; currency={txn.currency}; reference={txn.reference}"
        _create_exception(ledger_doc.client, ledger_batch, txn, "ledger", kind, title, description)
        exception_count += 1

    bank_doc.status = "Reconciled"
    bank_doc.save()
    ledger_doc.status = "Reconciled"
    ledger_doc.save()
    _audit("RECONCILIATION_COMPLETED", "LedgerOps Import Batch", bank_batch,
           f"ledger_batch={ledger_batch}; matches={created_matches}; exceptions={exception_count}; date_window_days={window}")

    return {
        "bank_batch": bank_batch,
        "ledger_batch": ledger_batch,
        "proposed_matches": created_matches,
        "exceptions_created": exception_count,
        "date_window_days": window,
        "matching_rule": "unique exact amount + currency + normalized reference + date window",
    }
