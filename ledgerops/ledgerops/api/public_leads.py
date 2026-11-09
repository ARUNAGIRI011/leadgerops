"""Public website lead capture with conservative validation and throttling."""
from __future__ import annotations

import re
import frappe
from frappe import _
from frappe.utils import strip_html


PRIVACY_NOTICE_VERSION = "2026-11-09"


def _clean(value, limit):
    return strip_html(str(value or "")).strip()[:limit]


@frappe.whitelist(allow_guest=True, methods=["POST"])
def submit_demo_request(name: str, email: str, company: str, country: str = "",
                        phone: str = "", team_size: str = "", client_count: str = "",
                        message: str = "", consent: str = "", website: str = ""):
    """Create a CRM lead from the public landing page; no customer data/files accepted."""
    # Honeypot field: silently reject automated form submissions.
    if website:
        return {"ok": True, "message": "Thank you. Your request has been received."}

    # Use the server-observed peer address. Do not trust a caller-supplied forwarding header
    # unless the reverse-proxy trust chain has been explicitly configured. 
    ip = frappe.local.request.remote_addr or "unknown"
    cache = frappe.cache()
    key = "ledgerops:demo-request:" + frappe.generate_hash(ip, length=24)
    try:
        count = cache.incr(key)
        if count == 1:
            cache.expire(key, 3600)
    except Exception:
        # Fail closed if the throttle backend is unavailable.
        frappe.log_error("Lead capture throttle unavailable", "LedgerOps public lead capture")
        frappe.throw(_("Please try again later"))

    if count > 5:
        frappe.local.response.http_status_code = 429
        frappe.throw(_("Too many requests. Please try again later."))

    name = _clean(name, 120)
    email = _clean(email, 180).lower()
    company = _clean(company, 160)
    country = _clean(country, 80)
    phone = _clean(phone, 40)
    message = _clean(message, 1500)

    if not name or not company or not re.fullmatch(r"[^@ ]+@[^@ ]+[.][^@ ]+", email):
        frappe.throw(_("Enter your name, company and a valid business email"))
    if consent not in ("1", "true", "on", "yes"):
        frappe.throw(_("Please accept the privacy notice to request a demo"))

    def _bounded_int(value, default=0):
        try:
            return max(0, min(int(value or default), 100000))
        except (TypeError, ValueError):
            return default

    existing = frappe.db.get_value("LedgerOps Lead", {"email": email, "status": ["not in", ["Won", "Lost"]]}, "name")
    if existing:
        frappe.db.set_value("LedgerOps Lead", existing, {
            "lead_name": name, "company": company, "country": country,
            "phone": phone, "pain_points": message, "consent_to_contact": 1,
            "privacy_notice_version": PRIVACY_NOTICE_VERSION,
        })
        lead_name = existing
    else:
        doc = frappe.get_doc({
            "doctype": "LedgerOps Lead",
            "lead_name": name,
            "email": email,
            "company": company,
            "country": country,
            "phone": phone,
            "source": "Website",
            "status": "New",
            "team_size": _bounded_int(team_size),
            "client_count": _bounded_int(client_count),
            "pain_points": message,
            "consent_to_contact": 1,
            "privacy_notice_version": PRIVACY_NOTICE_VERSION,
        })
        doc.insert(ignore_permissions=True)
        lead_name = doc.name

    return {"ok": True, "message": "Thank you. Our team will contact you about a LedgerOps demo.", "lead_reference": lead_name}
