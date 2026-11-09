"""Authenticated CSV import endpoints for LedgerOps."""
from __future__ import annotations

import hashlib

import frappe
from frappe import _
from ledgerops.ledgerops.services.csv_import import parse_csv_content


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


@frappe.whitelist()
def import_csv(client: str, source_type: str, csv_text: str, source_filename: str = ""):
    """Import CSV text into a staged bank or ledger batch.

    POST /api/method/ledgerops.ledgerops.api.imports.import_csv
    Max payload: 5 MiB; max rows: 10,000. A private File upload/background-job
    pipeline is a follow-on for larger files.
    """
    if source_type not in ("Bank Statement", "Ledger Export"):
        frappe.throw(_("source_type must be Bank Statement or Ledger Export"))
    _require_create("LedgerOps Import Batch")
    transaction_doctype = (
        "LedgerOps Bank Transaction" if source_type == "Bank Statement"
        else "LedgerOps Ledger Transaction"
    )
    _require_create(transaction_doctype)
    _require_create("LedgerOps Audit Event")

    client_doc = frappe.get_doc("LedgerOps Client", client)
    client_doc.check_permission("read")
    try:
        rows = parse_csv_content(csv_text)
    except ValueError as exc:
        frappe.throw(str(exc))

    digest = hashlib.sha256(csv_text.encode("utf-8")).hexdigest()
    batch = frappe.get_doc({
        "doctype": "LedgerOps Import Batch",
        "client": client,
        "source_type": source_type,
        "status": "Processing",
        "source_filename": (source_filename or "")[:140],
        "source_sha256": digest,
        "row_count": len(rows),
    }).insert()

    for row in rows:
        frappe.get_doc({
            "doctype": transaction_doctype,
            "import_batch": batch.name,
            "client": client,
            "source_row_number": row.source_row_number,
            "transaction_date": row.transaction_date.isoformat(),
            "description": row.description,
            "reference": row.reference,
            "amount_minor": row.amount_minor,
            "currency": row.currency,
            "matched": 0,
        }).insert()

    batch.status = "Imported"
    batch.save()
    _audit("CSV_IMPORTED", "LedgerOps Import Batch", batch.name,
           f"{source_type}; rows={len(rows)}; sha256={digest}")
    return {"batch": batch.name, "source_type": source_type, "row_count": len(rows), "sha256": digest}
