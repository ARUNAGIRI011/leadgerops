# Product scope and roadmap

## Target workflow

1. Firm staff creates a client and accounting period/engagement.
2. Staff uploads bank statement and ledger export.
3. Import preview validates columns, dates, currencies and row counts.
4. Deterministic engine proposes unique matches and raises exceptions for unmatched/ambiguous/duplicate/difference cases.
5. Staff requests evidence from the client and links uploaded files to the exception.
6. Preparer resolves; reviewer approves; audit history records each action.
7. Firm views exception ageing and period close status.

## MVP P0

- Firm/client/team and role model.
- Import batch, CSV mapping and validation preview.
- Bank/ledger transaction staging with source-row provenance.
- Deterministic one-to-one matching using integer minor units.
- Exceptions for unmatched, duplicates, and amount/date differences.
- Evidence request, private attachment and assignment.
- Status transitions, reviewer approval and immutable audit events.
- Period dashboard and exportable close report.

## P1

- Client portal and email notifications.
- Cloudflare Workers AI explanation/message drafts (human review required).
- Multi-currency and configurable matching policies.
- Tally/Zoho Books/QuickBooks/Xero integrations after validating APIs and partner terms.

## P2

- OCR/document extraction, advanced analytics, multi-entity consolidation.

## Explicitly out of scope

- General ledger, journal posting, tax filing, statutory audit opinion, investment advice.
- LLM-based reconciliation decisions or autonomous posting.

## Validation gates (proposed, not market benchmarks)

Interview 15–20 firms, secure 3–5 design partners, run real workflows only with consent and data-processing terms, and seek at least two paid pilots before expanding scope. Validate willingness to pay and time saved rather than treating downloads or sign-ups as product-market fit.
