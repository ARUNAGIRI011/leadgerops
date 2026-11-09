"""Internal product-owner metrics and CRM dashboard APIs."""
from __future__ import annotations

import frappe
from frappe import _


OWNER_ROLES = {"System Manager", "LedgerOps Product Owner"}


def _require_owner():
    if not (set(frappe.get_roles()) & OWNER_ROLES):
        frappe.throw(_("Product-owner access is required"), frappe.PermissionError)


@frappe.whitelist()
def get_overview():
    _require_owner()
    count = lambda dt, filters=None: frappe.db.count(dt, filters=filters or {})
    mrr = frappe.db.sql(
        """select currency, sum(monthly_recurring_revenue) as amount
           from `tabLedgerOps Account`
           where lifecycle_status in ('Active', 'At Risk')
           group by currency order by currency""",
        as_dict=True,
    )
    pipeline = frappe.db.sql(
        """select currency, sum(estimated_monthly_value) as amount
           from `tabLedgerOps Lead`
           where status not in ('Won', 'Lost')
           group by currency order by currency""",
        as_dict=True,
    )
    leads_by_stage = frappe.db.sql(
        """select status, count(*) as total
           from `tabLedgerOps Lead`
           group by status order by total desc""",
        as_dict=True,
    )
    recent_leads = frappe.get_all(
        "LedgerOps Lead",
        fields=["name", "lead_name", "company", "email", "country", "status", "source", "creation"],
        order_by="creation desc",
        limit_page_length=8,
    )
    renewals = frappe.get_all(
        "LedgerOps Subscription",
        filters={"status": ["in", ["Active", "Trialing", "Past Due"]]},
        fields=["name", "account", "plan_name", "status", "amount", "currency", "current_period_end"],
        order_by="current_period_end asc",
        limit_page_length=8,
    )
    return {
        "leads": count("LedgerOps Lead"),
        "open_leads": count("LedgerOps Lead", {"status": ["not in", ["Won", "Lost"]]}),
        "customers": count("LedgerOps Account"),
        "active_customers": count("LedgerOps Account", {"lifecycle_status": "Active"}),
        "open_support_cases": count("LedgerOps Support Case", {"status": ["not in", ["Resolved", "Closed"]]}),
        "subscriptions": count("LedgerOps Subscription"),
        "active_subscriptions": count("LedgerOps Subscription", {"status": "Active"}),
        "mrr_by_currency": mrr,
        "pipeline_by_currency": pipeline,
        "leads_by_stage": leads_by_stage,
        "recent_leads": recent_leads,
        "upcoming_renewals": renewals,
    }


@frappe.whitelist()
def list_customers(search: str = "", lifecycle_status: str = "", limit_start: int = 0, page_length: int = 20):
    _require_owner()
    filters = {}
    if lifecycle_status:
        filters["lifecycle_status"] = lifecycle_status
    or_filters = None
    if search:
        term = "%" + frappe.db.escape(search.strip()[:80], percent=True) + "%"
        or_filters = [
            ["LedgerOps Account", "account_name", "like", term],
            ["LedgerOps Account", "primary_email", "like", term],
            ["LedgerOps Account", "country", "like", term],
        ]
    return frappe.get_list(
        "LedgerOps Account",
        filters=filters,
        or_filters=or_filters,
        fields=["name", "account_name", "account_type", "primary_email", "country", "lifecycle_status", "plan", "monthly_recurring_revenue", "currency", "renewal_date"],
        order_by="modified desc",
        start=max(0, int(limit_start)),
        page_length=min(max(1, int(page_length)), 100),
    )
