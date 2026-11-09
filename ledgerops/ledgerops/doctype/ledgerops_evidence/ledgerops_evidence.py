from frappe.model.document import Document
import frappe


class LedgerOpsEvidence(Document):
    def before_insert(self):
        self.uploaded_by = frappe.session.user

    def validate(self):
        if self.file:
            file_doc = frappe.get_doc("File", {"file_url": self.file})
            if not file_doc.is_private:
                frappe.throw("LedgerOps evidence must be stored as a private File")
            if file_doc.attached_to_doctype not in (None, "", "LedgerOps Evidence"):
                frappe.throw("Evidence file is already attached to another document")
