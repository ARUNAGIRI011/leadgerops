"""Permission-aware summary counters for the Desk dashboard."""
import frappe
from frappe import _


@frappe.whitelist()
def get_overview():
    allowed = {"System Manager", "LedgerOps Admin", "LedgerOps Manager", "LedgerOps Accountant", "LedgerOps Reviewer"}
    if not (set(frappe.get_roles()) & allowed):
        frappe.throw(_("You do not have access to the LedgerOps dashboard"), frappe.PermissionError)

    def count(doctype, filters):
        return frappe.db.count(doctype, filters=filters)

    return {
        "open_exceptions": count("LedgerOps Exception", {"status": "Open"}),
        "in_progress": count("LedgerOps Exception", {"status": "In Progress"}),
        "waiting_for_client": count("LedgerOps Exception", {"status": "Waiting for Client"}),
        "resolved": count("LedgerOps Exception", {"status": ["in", ["Resolved", "Approved"]]}),
        "evidence_items": count("LedgerOps Evidence", {}),
    }
