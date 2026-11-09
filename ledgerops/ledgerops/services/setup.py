"""Install-time LedgerOps role and permission provisioning."""
import frappe
from frappe.permissions import add_permission, update_permission_property

BASE_ROLES = ("LedgerOps Admin", "LedgerOps Manager", "LedgerOps Accountant", "LedgerOps Reviewer")
CRM_ROLES = (
    "LedgerOps Product Owner",
    "LedgerOps Sales Manager",
    "LedgerOps Sales Representative",
    "LedgerOps Customer Success",
    "LedgerOps Support Agent",
)
ROLE_NAMES = BASE_ROLES + CRM_ROLES

ACCOUNTING_DOCTYPES = (
    "LedgerOps Client", "LedgerOps Import Batch", "LedgerOps Bank Transaction",
    "LedgerOps Ledger Transaction", "LedgerOps Match", "LedgerOps Exception",
    "LedgerOps Evidence Request", "LedgerOps Evidence", "LedgerOps Audit Event",
)
FULL = {"read": 1, "write": 1, "create": 1, "delete": 0, "report": 1, "export": 0, "share": 0}
READ_ONLY = {"read": 1, "write": 0, "create": 0, "delete": 0, "report": 1, "export": 0, "share": 0}

# Fail closed for Sales Representatives until owner-scoped list/document permission
# hooks and tests are implemented. Giving DocType-wide read access would expose
# every lead in the CRM, not just the representative's assigned leads.
CRM_ACCESS = {
    "LedgerOps Lead": {
        "LedgerOps Admin": FULL,
        "LedgerOps Product Owner": FULL,
        "LedgerOps Sales Manager": FULL,
    },
    "LedgerOps Account": {
        "LedgerOps Admin": FULL,
        "LedgerOps Product Owner": FULL,
        "LedgerOps Sales Manager": FULL,
        "LedgerOps Customer Success": FULL,
        "LedgerOps Support Agent": READ_ONLY,
    },
    "LedgerOps Contact": {
        "LedgerOps Admin": FULL,
        "LedgerOps Product Owner": FULL,
        "LedgerOps Sales Manager": FULL,
        "LedgerOps Customer Success": FULL,
        "LedgerOps Support Agent": READ_ONLY,
    },
    "LedgerOps CRM Activity": {
        "LedgerOps Admin": FULL,
        "LedgerOps Product Owner": FULL,
        "LedgerOps Sales Manager": FULL,
        "LedgerOps Customer Success": FULL,
    },
    "LedgerOps Subscription": {
        "LedgerOps Admin": FULL,
        "LedgerOps Product Owner": FULL,
        "LedgerOps Sales Manager": READ_ONLY,
        "LedgerOps Customer Success": READ_ONLY,
    },
    "LedgerOps Support Case": {
        "LedgerOps Admin": FULL,
        "LedgerOps Product Owner": FULL,
        "LedgerOps Sales Manager": FULL,
        "LedgerOps Customer Success": FULL,
        "LedgerOps Support Agent": FULL,
    },
}


def _grant(doctype, role, permissions):
    if not frappe.db.exists("DocType", doctype):
        return
    add_permission(doctype, role, 0)
    for permission_type, value in permissions.items():
        update_permission_property(doctype, role, 0, permission_type, value)


def after_install():
    for role_name in ROLE_NAMES:
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert(ignore_permissions=True)

    for doctype in ACCOUNTING_DOCTYPES:
        for role in BASE_ROLES:
            permissions = FULL
            if role == "LedgerOps Reviewer" and doctype in (
                "LedgerOps Import Batch", "LedgerOps Bank Transaction", "LedgerOps Ledger Transaction"
            ):
                permissions = READ_ONLY
            if doctype == "LedgerOps Audit Event":
                # Events are append-only through controlled server APIs.
                permissions = {"read": 1, "write": 0, "create": 1, "delete": 0, "report": 1, "export": 0, "share": 0}
            _grant(doctype, role, permissions)

    for doctype, role_permissions in CRM_ACCESS.items():
        for role, permissions in role_permissions.items():
            _grant(doctype, role, permissions)

    for page_name, title in (
        ("ledgerops-owner", "LedgerOps Owner Console"),
        ("ledgerops-dashboard", "LedgerOps Dashboard"),
    ):
        if not frappe.db.exists("Page", page_name):
            frappe.get_doc({
                "doctype": "Page",
                "page_name": page_name,
                "title": title,
                "module": "LedgerOps",
                "standard": "No",
                "system_page": 0,
            }).insert(ignore_permissions=True)


def after_migrate():
    after_install()
    frappe.clear_cache()
