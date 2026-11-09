"""Evidence record creation. Upload files through Frappe's authenticated private file API first."""
import frappe
from frappe import _


@frappe.whitelist()
def register_evidence(exception_name: str, file_url: str, file_label: str, notes: str = ""):
    roles = {"System Manager", "LedgerOps Admin", "LedgerOps Manager", "LedgerOps Accountant"}
    if not (set(frappe.get_roles()) & roles):
        frappe.throw(_("You do not have permission to register evidence"), frappe.PermissionError)
    exception = frappe.get_doc("LedgerOps Exception", exception_name)
    exception.check_permission("read")
    file_doc = frappe.get_doc("File", {"file_url": file_url})
    if not file_doc.is_private:
        frappe.throw(_("Evidence must be uploaded as a private file"))
    evidence = frappe.get_doc({
        "doctype": "LedgerOps Evidence",
        "exception": exception.name,
        "file_label": file_label[:140],
        "file": file_url,
        "notes": notes[:1000],
    })
    evidence.insert()
    frappe.get_doc({
        "doctype": "LedgerOps Audit Event",
        "actor": frappe.session.user,
        "action": "Evidence Registered",
        "reference_doctype": "LedgerOps Exception",
        "reference_name": exception.name,
        "details": f"evidence={evidence.name}; private_file=true",
    }).insert()
    return {"name": evidence.name, "file": file_url}
