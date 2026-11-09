# LedgerOps

**Reconciliation exceptions → client evidence → review → month-end close.**

LedgerOps is a Frappe-based workflow app for accounting and bookkeeping practices. It complements Tally, Zoho Books, QuickBooks, Xero and spreadsheet exports; it is not a general ledger, tax-filing engine or source of accounting truth.

> GitHub repository: `leadgerops` (spelled as created). Frappe/Python app: `ledgerops`.

## Current feature branch

Branch: `feature/desk-rbac-cloudflare-ai`

### Added in this milestone

- Desk dashboard with permission-checked exception and evidence counters.
- Exception form actions for AI explanation, client-message draft and reviewer summary.
- Cloudflare Workers AI REST client using the OpenAI-compatible Chat Completions endpoint.
- AI prompts send only exception type, title, description, status and priority; client names, bank references, transaction IDs and uploaded files are excluded.
- AI output is advisory text only. It cannot match transactions, resolve exceptions, approve work or post accounting entries.
- Private evidence register DocType and API to associate an already uploaded private Frappe File with an exception.
- Install/migrate hooks create LedgerOps roles and permission records.

## Cloudflare Workers AI setup

Configure the following values in the Frappe site's `site_config.json` using `bench --site <site-name> set-config`:

```bash
bench --site <site-name> set-config cloudflare_workers_ai_account_id <CLOUDFLARE_ACCOUNT_ID>
bench --site <site-name> set-config cloudflare_workers_ai_api_token <CLOUDFLARE_API_TOKEN>
bench --site <site-name> set-config cloudflare_workers_ai_model @cf/zai-org/glm-4.7-flash
```

Use a Cloudflare API token scoped to Workers AI inference for the intended account. Never commit the token, expose it in browser JavaScript, or return it through a whitelisted endpoint. Rotate it if it is ever exposed.

Current default model is `@cf/zai-org/glm-4.7-flash`; Cloudflare's current model catalog and account plan must be checked before production. Cloudflare documents 10,000 free Neurons/day, resetting at 00:00 UTC. Requests fail after the free quota is exhausted on Workers Free; Workers Paid currently charges $0.011 per 1,000 Neurons above the daily included allocation. Some models require a paid plan or prepaid AI Gateway credits. See [Workers AI pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/) and [Workers AI overview](https://developers.cloudflare.com/workers-ai/).

The Frappe endpoint is:

`POST /api/method/ledgerops.ledgerops.api.ai.assist_exception`

JSON body:

```json
{"exception_name":"<exception-id>","task":"explain"}
```

Allowed task values: `explain`, `client_message`, `close_summary`.

## Roles and tenancy

Roles created: LedgerOps Admin, LedgerOps Manager, LedgerOps Accountant, LedgerOps Reviewer. Existing System Manager access remains available.

**MVP tenant boundary: one Frappe site per accounting firm.** The role setup is site-local; this branch does not implement shared-database tenant_id isolation. Do not place multiple firms in one Frappe site until tenant-aware permission query conditions and cross-tenant API tests have been implemented.

## Evidence workflow

1. Upload the file through Frappe's authenticated file upload endpoint with private storage enabled.
2. Call `POST /api/method/ledgerops.ledgerops.api.evidence.register_evidence` with `exception_name`, `file_url`, `file_label` and optional `notes`.
3. The API rejects non-private files, links the File record to the Evidence document and creates an audit event.

Test private download permissions with two separate users before any client pilot. The evidence API is not a public client portal.

## Existing reconciliation workflow

- CSV parser with date/amount/currency validation, source-row numbers, 5 MiB payload cap and 10,000-row cap.
- CSV import API that records SHA-256 provenance and stages transactions.
- Deterministic one-to-one matching: exact signed amount in minor units + currency + normalized reference + date tolerance.
- Proposed matches and review exceptions for unmatched, ambiguous, amount/date differences and duplicate fingerprints.
- No partial, one-to-many, many-to-many, FX, fuzzy or opposite-sign matching.

## Validation status and limitations

- This branch has not been installed against a live Frappe v16 site in this environment.
- Frappe DocType migration, role-permission setup, Desk JS, private file upload/download and Cloudflare API calls require live-site integration tests.
- No GitHub Actions run has been independently verified; do not treat this as a passing CI build.
- Dashboard counters are basic; assignment ageing charts, client portal, email delivery and reviewer approval state machine are not complete.
- AI responses are untrusted drafts. A human must verify them before sending or using them.
- Cloudflare quota, model availability and per-model rate limits are account- and model-dependent; exact per-customer capacity requires load testing.
- Synchronous import/reconciliation is capped at 10,000 rows per batch. Larger jobs need background workers and idempotent chunk processing.

## Development

Use a Frappe Bench with Frappe v16 and optional ERPNext on the same major branch:

```bash
bench get-app https://github.com/ARUNAGIRI011/leadgerops --branch feature/desk-rbac-cloudflare-ai
bench --site <site-name> install-app ledgerops
bench --site <site-name> migrate
bench --site <site-name> run-tests --app ledgerops
```

Pure Python tests:

```bash
python -m pip install pytest
python -m pytest -q tests
```

Do not mix Frappe/ERPNext major branches. Confirm the current official installation matrix for Python, Node, MariaDB, Redis and OS packages before provisioning.

## Security

Use synthetic data only during development. Keep API credentials server-side. Evidence files must be private. The initial design assumes a separate site per firm; tenant isolation, backup/restore, retention, incident response and restore tests are still required before production.

## License

MIT for this custom app code. Frappe Framework and optional ERPNext retain their own licenses. Review dependency and distribution obligations before commercial distribution.
