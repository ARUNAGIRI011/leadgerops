"""Install-time roles and a basic Desk landing page for LedgerOps."""
import frappe

ROLE_NAMES = ("LedgerOps Admin", "LedgerOps Manager", "LedgerOps Accountant", "LedgerOps Reviewer")


def after_install():
    for role_name in ROLE_NAMES:
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert(ignore_permissions=True)
    if not frappe.db.exists("Page", "ledgerops-dashboard"):
        frappe.get_doc({
            "doctype": "Page",
            "page_name": "ledgerops-dashboard",
            "title": "LedgerOps Dashboard",
            "module": "LedgerOps",
            "standard": "Yes",
            "system_page": 0,
        }).insert(ignore_permissions=True)


def after_migrate():
    # The app uses a separate Frappe site per accounting firm as the initial tenant boundary.
    after_install()
