# Architecture

## Logical components

- Frappe web application: identity, DocTypes, role checks, workflow UI and REST endpoints.
- LedgerOps domain services: import validation, normalization, deterministic reconciliation, exception lifecycle.
- MariaDB: transactional records and audit events, through Frappe ORM.
- Redis: background jobs and cache as managed by Bench.
- Private file storage: client evidence; use access-controlled downloads and retention policy.
- Cloudflare Workers AI: optional server-side text assistant, isolated behind an adapter.

## Integration boundary

LedgerOps consumes exports first. Existing accounting products remain systems of record. ERPNext may be installed alongside LedgerOps for customers who want it, but LedgerOps must not require ERPNext.

## Reconciliation safety

Use integer minor currency units, explicit currency codes, deterministic rules and explainable rule IDs. Auto-match only when the candidate is unique on both sides. Ambiguous candidates become review exceptions. Never use an LLM to calculate amounts, choose ledger postings or auto-resolve exceptions.

## Tenancy

For the first controlled deployment, prefer one Frappe site/database per firm. This is an operational isolation strategy, not automatic SaaS readiness: automate provisioning, backups, patching, monitoring, tenant-level usage limits and restore tests before scaling. Shared-site multi-tenancy requires explicit server-side tenant scoping and security tests.

## Deployment

Use Bench-managed Frappe services. Keep Frappe and optional ERPNext on the same major branch. Production needs HTTPS, MariaDB backups, Redis, worker processes, scheduler, private file storage, monitoring and tested restore procedures. Exact capacity and monthly cost require workload tests and provider quotes.
