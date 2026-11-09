"""Install-time roles, permissions and a basic Desk landing page."""
import frappe
from frappe.permissions import add_permission, update_permission_property

ROLE_NAMES = ("LedgerOps Admin", "LedgerOps Manager", "LedgerOps Accountant", "LedgerOps Reviewer")
DOCTYPE_NAMES = (
    "LedgerOps Client",
    "LedgerOps Import Batch",
    "LedgerOps Bank Transaction",
    "LedgerOps Ledger Transaction",
    "LedgerOps Match",
    "LedgerOps Exception",
    "LedgerOps Evidence Request",
    "LedgerOps Evidence",
    "LedgerOps Audit Event",
)

# One Frappe site per accounting firm is the MVP tenant boundary. These roles
# are site-local and do not implement shared-database multi-tenancy.
PERMISSIONS = {
    "LedgerOps Admin": {"read": 1, "write": 1, "create": 1, "delete": 0, "report": 1, "export": 0, "share": 0},
    "LedgerOps Manager": {"read": 1, "write": 1, "create": 1, "delete": 0, "report": 1, "export": 0, "share": 0},
    "LedgerOps Accountant": {"read": 1, "write": 1, "create": 1, "delete": 0, "report": 0, "export": 0, "share": 0},
    "LedgerOps Reviewer": {"read": 1, "write": 1, "create": 0, "delete": 0, "report": 1, "export": 0, "share": 0},
}


def after_install():
    for role_name in ROLE_NAMES:
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert(ignore_permissions=True)

    for doctype in DOCTYPE_NAMES:
        if not frappe.db.exists("DocType", doctype):
            continue
        for role_name, permissions in PERMISSIONS.items():
            if role_name == "LedgerOps Reviewer" and doctype in (
                "LedgerOps Import Batch", "LedgerOps Bank Transaction", "LedgerOps Ledger Transaction"
            ):
                # Reviewer can inspect source data but cannot edit/import it.
                permissions = {**permissions, "write": 0, "create": 0}
            if doctype == "LedgerOps Audit Event":
                # API endpoints append audit events; roles cannot edit or delete them.
                permissions = {"read": 1, "write": 0, "create": 1, "delete": 0, "report": 1, "export": 0, "share": 0}
            add_permission(doctype, role_name, 0)
            for ptype, value in permissions.items():
                update_permission_property(doctype, role_name, 0, ptype, value)

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
    after_install()
    frappe.clear_cache()
