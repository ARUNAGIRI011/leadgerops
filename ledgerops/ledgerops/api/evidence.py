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
    file_name = frappe.db.get_value("File", {"file_url": file_url}, "name")
    if not file_name:
        frappe.throw(_("Uploaded file record was not found"))
    file_doc = frappe.get_doc("File", file_name)
    if not file_doc.is_private:
        frappe.throw(_("Evidence must be uploaded as a private file"))
    if file_doc.owner != frappe.session.user and "System Manager" not in frappe.get_roles():
        frappe.throw(_("You can register only evidence files that you uploaded"), frappe.PermissionError)
    if file_doc.attached_to_doctype == "LedgerOps Exception" and file_doc.attached_to_name != exception.name:
        frappe.throw(_("Evidence file is attached to a different exception"), frappe.PermissionError)
    if file_doc.attached_to_doctype not in (None, "", "LedgerOps Exception"):
        frappe.throw(_("Evidence file is already linked to another document"), frappe.PermissionError)

    evidence = frappe.get_doc({
        "doctype": "LedgerOps Evidence",
        "exception": exception.name,
        "file_label": file_label[:140],
        "file": file_url,
        "notes": notes[:1000],
    })
    evidence.insert()
    file_doc.db_set({
        "attached_to_doctype": "LedgerOps Evidence",
        "attached_to_name": evidence.name,
        "attached_to_field": "file",
    })
    frappe.get_doc({
        "doctype": "LedgerOps Audit Event",
        "actor": frappe.session.user,
        "action": "Evidence Registered",
        "reference_doctype": "LedgerOps Exception",
        "reference_name": exception.name,
        "details": f"evidence={evidence.name}; private_file=true",
    }).insert()
    return {"name": evidence.name, "file": file_url}
