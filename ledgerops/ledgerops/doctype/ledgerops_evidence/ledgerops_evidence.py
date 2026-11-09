from frappe.model.document import Document
import frappe


class LedgerOpsEvidence(Document):
    def before_insert(self):
        self.uploaded_by = frappe.session.user

    def validate(self):
        if not self.file:
            frappe.throw("A private evidence file is required")
        file_name = frappe.db.get_value("File", {"file_url": self.file}, "name")
        if not file_name:
            frappe.throw("Evidence file record was not found")
        file_doc = frappe.get_doc("File", file_name)
        if not file_doc.is_private:
            frappe.throw("LedgerOps evidence must be stored as a private File")
