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
CRM_DOCTYPES = (
    "LedgerOps Lead", "LedgerOps Account", "LedgerOps Contact",
    "LedgerOps CRM Activity", "LedgerOps Subscription", "LedgerOps Support Case",
)
FULL = {"read": 1, "write": 1, "create": 1, "delete": 0, "report": 1, "export": 0, "share": 0}
READ_ONLY = {"read": 1, "write": 0, "create": 0, "delete": 0, "report": 1, "export": 0, "share": 0}

CRM_ACCESS = {
    "LedgerOps Lead": ("LedgerOps Admin", "LedgerOps Product Owner", "LedgerOps Sales Manager", "LedgerOps Sales Representative"),
    "LedgerOps Account": ("LedgerOps Admin", "LedgerOps Product Owner", "LedgerOps Sales Manager", "LedgerOps Customer Success", "LedgerOps Support Agent"),
    "LedgerOps Contact": ("LedgerOps Admin", "LedgerOps Product Owner", "LedgerOps Sales Manager", "LedgerOps Sales Representative", "LedgerOps Customer Success", "LedgerOps Support Agent"),
    "LedgerOps CRM Activity": ("LedgerOps Admin", "LedgerOps Product Owner", "LedgerOps Sales Manager", "LedgerOps Sales Representative", "LedgerOps Customer Success"),
    "LedgerOps Subscription": ("LedgerOps Admin", "LedgerOps Product Owner", "LedgerOps Sales Manager", "LedgerOps Customer Success"),
    "LedgerOps Support Case": ("LedgerOps Admin", "LedgerOps Product Owner", "LedgerOps Sales Manager", "LedgerOps Customer Success", "LedgerOps Support Agent"),
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

    for doctype, roles in CRM_ACCESS.items():
        for role in roles:
            _grant(doctype, role, FULL)

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
