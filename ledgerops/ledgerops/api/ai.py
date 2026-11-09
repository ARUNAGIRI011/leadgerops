"""Advisory-only AI endpoints for LedgerOps."""
from __future__ import annotations

import frappe
from frappe import _

from ledgerops.ledgerops.services.cloudflare_ai import generate_exception_assistance


ALLOWED_ROLES = {"System Manager", "LedgerOps Admin", "LedgerOps Manager", "LedgerOps Accountant", "LedgerOps Reviewer"}


def _require_ledgerops_role():
    if not (set(frappe.get_roles()) & ALLOWED_ROLES):
        frappe.throw(_("You do not have access to LedgerOps AI"), frappe.PermissionError)


@frappe.whitelist()
def assist_exception(exception_name: str, task: str = "explain"):
    """Return an AI explanation, client-message draft, or reviewer summary; never changes records."""
    _require_ledgerops_role()
    doc = frappe.get_doc("LedgerOps Exception", exception_name)
    doc.check_permission("read")
    result = generate_exception_assistance(doc, task)
    # Log metadata only; never persist the prompt or exception contents in the audit event.
    frappe.get_doc({
        "doctype": "LedgerOps Audit Event",
        "actor": frappe.session.user,
        "action": "AI Assistance Generated",
        "reference_doctype": "LedgerOps Exception",
        "reference_name": doc.name,
        "details": f"task={task}; model={result['model']}; advisory_only=true",
    }).insert(ignore_permissions=False)
    return result
