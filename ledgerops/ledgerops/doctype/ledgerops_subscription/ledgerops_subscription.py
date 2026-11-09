import re
import frappe
from frappe.model.document import Document


class LedgerOpsSubscription(Document):
    def validate(self):
        if self.currency and not re.fullmatch(r"[A-Z]{3}", self.currency.upper()):
            frappe.throw("Currency must be a three-letter ISO-style code such as INR, USD or EUR")
        if self.currency:
            self.currency = self.currency.upper()
        if self.amount is not None and self.amount < 0:
            frappe.throw("Subscription amount cannot be negative")
