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
        "in_review": count("LedgerOps Exception", {"status": "In Review"}),
        "resolved": count("LedgerOps Exception", {"status": "Resolved"}),
        "evidence_items": count("LedgerOps Evidence", {}),
    }
