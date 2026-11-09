import re
import frappe
from frappe.model.document import Document


class LedgerOpsLead(Document):
    def validate(self):
        if self.currency and not re.fullmatch(r"[A-Z]{3}", self.currency.upper()):
            frappe.throw("Currency must be a three-letter ISO-style code such as INR, USD or EUR")
        if self.currency:
            self.currency = self.currency.upper()
        if self.estimated_monthly_value is not None and self.estimated_monthly_value < 0:
            frappe.throw("Estimated monthly value cannot be negative")
