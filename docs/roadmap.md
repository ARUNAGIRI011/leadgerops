# Product scope and roadmap

## Implemented in current bootstrap branch

- Frappe DocTypes for clients, import batches, staged bank/ledger rows, proposed matches, exceptions, evidence requests and audit events.
- CSV text parser with date, amount and currency validation, SHA-256 batch provenance and source-row numbering.
- Deterministic one-to-one matching by unique exact signed amount, currency, normalized reference and date window.
- Exceptions for unmatched rows, ambiguity, amount/date differences and duplicate fingerprints.
- Starter pure-Python tests for parser and matching services.

## Next P0 work

1. Install/migrate on a real Frappe v16 bench and validate every DocType JSON/controller.
2. Add firm/site provisioning, staff roles and permission tests; replace System Manager-only access.
3. Build Desk UI for imports, exception queues, assignments, comments, evidence requests and reviewer approvals.
4. Implement private evidence upload/download with authorization checks and audit trail.
5. Add background/chunked import and reconciliation with idempotency and retry safety.
6. Add Frappe integration tests, CI execution and backup/restore tests.

## P1

- Client portal and email notifications.
- Cloudflare Workers AI explanation/message drafts (human review required).
- Multi-currency and configurable matching policies.
- Tally/Zoho Books/QuickBooks/Xero integrations after validating APIs and partner terms.

## P2

- OCR/document extraction, advanced analytics and multi-entity consolidation.

## Explicitly out of scope

General ledger, journal posting, tax filing, statutory audit opinion, investment advice, LLM-based reconciliation decisions and autonomous posting.

## Validation gates (proposed, not market benchmarks)

Interview 15–20 firms, secure 3–5 design partners, run real workflows only with consent and data-processing terms, and seek at least two paid pilots before expanding scope. Validate willingness to pay and time saved rather than treating downloads or sign-ups as product-market fit.
