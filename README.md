# LedgerOps

**Reconciliation exceptions → client evidence → review → month-end close.**

LedgerOps is an open-source, Frappe-based workflow app for accounting and bookkeeping practices. It complements existing accounting systems (Tally, Zoho Books, QuickBooks, Xero and spreadsheets); it is not a general ledger, tax-filing engine or source of accounting truth.

> Repository name: `leadgerops` (as created in GitHub). Python/Frappe app name: `ledgerops`.

## MVP scope

- Import bank and ledger CSV exports with an auditable import batch.
- Normalize transaction rows and run deterministic reconciliation.
- Surface unmatched, duplicate and amount/date-difference exceptions.
- Request and attach supporting evidence to exceptions.
- Assign, comment, resolve/reopen and reviewer-approve work.
- Track status, ageing and month-end progress.
- Optional AI drafts/explanations only; AI never calculates matches or posts accounting entries.

## Architecture

- Frappe Framework custom app: DocTypes, authentication, roles/permissions, REST APIs, background jobs and UI.
- MariaDB using the standard Frappe deployment path; Redis for queues/cache.
- Private Frappe file storage for evidence (production object-storage integration is a deployment decision).
- Cloudflare Workers AI behind a server-side adapter for optional text assistance.
- ERPNext is optional. Do not fork or modify ERPNext core.

## Repository layout

```
ledgerops/
├── ledgerops/
│   ├── hooks.py
│   ├── modules.txt
│   └── ledgerops/
│       ├── api/
│       ├── doctype/
│       └── services/
├── docs/
├── samples/
└── tests/
```

## Development setup

Use a Frappe Bench environment. Pin Frappe and ERPNext to the same supported major branch; the initial compatibility target is **Frappe/ERPNext v16**. Confirm the current v16 installation prerequisites on the official docs before provisioning a server.

```bash
# In a supported Frappe Bench directory
bench get-app https://github.com/ARUNAGIRI011/leadgerops --branch bootstrap/ledgerops-mvp
bench --site <site-name> install-app ledgerops
bench --site <site-name> migrate
bench --site <site-name> list-apps
```

If creating a fresh bench, install the matching Frappe and (optionally) ERPNext v16 branches first. Never mix major branches.

## Current implementation status

This bootstrap commit establishes the custom app package, product/architecture docs, deterministic matching service and starter tests. It is **not yet a production-ready SaaS**. CSV ingestion UI, full DocType workflows, tenant provisioning, permissions audit, notifications, AI adapter, deployment automation and end-to-end tests remain planned.

## Design principles

1. Money/date matching is deterministic and testable; no LLM makes accounting decisions.
2. Ambiguous matches go to human review.
3. Store source rows and import-batch provenance; never silently overwrite imported data.
4. Every state transition and reviewer action must be auditable.
5. Firm data isolation must be enforced server-side, not by hiding UI fields.
6. Start with synthetic data. Do not upload real PAN, Aadhaar or bank data to development/demo environments.

## Documentation

- [Product scope and roadmap](docs/roadmap.md)
- [Architecture](docs/architecture.md)
- [Data model](docs/data-model.md)
- [Security baseline](docs/security.md)
- [Local development and testing](docs/development.md)

## License

MIT for this custom app code. Frappe Framework and any optional ERPNext installation retain their own respective licenses. Review dependency and distribution obligations before commercial distribution.
