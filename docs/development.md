# Development and test guide

## Prerequisites

- Frappe Bench with Frappe v16; optional ERPNext must use the same major branch.
- Install Python, Node, MariaDB, Redis and OS packages from the current official Frappe v16 installation matrix. Exact patch versions depend on the deployment OS and are not pinned by this repository.

## Install

```bash
bench get-app https://github.com/ARUNAGIRI011/leadgerops --branch bootstrap/ledgerops-mvp
bench --site <site-name> install-app ledgerops
bench --site <site-name> migrate
bench --site <site-name> run-tests --app ledgerops
```

## Pure-Python tests

```bash
python -m pip install pytest
python -m pytest -q tests
```

## CSV import API

Create a `LedgerOps Client` using the standard Frappe resource API. Then POST JSON to:

`/api/method/ledgerops.ledgerops.api.imports.import_csv`

Fields: `client`, `source_type` (`Bank Statement` or `Ledger Export`), `csv_text`, optional `source_filename`.

Supported columns:
- Date: `transaction_date`, `posting_date` or `date`.
- Amount: `amount`, or both `debit` and `credit`.
- Optional: `description`/`narration`, `reference`/`utr`/`transaction_id`, `currency`.

Dates accepted: ISO `YYYY-MM-DD` or `DD/MM/YYYY`. Amounts use two decimal places and convert to integer minor units. Credit is positive; debit is negative. Currency defaults to INR and must be a three-letter alphabetic code.

Limits: 5 MiB UTF-8 CSV text, 10,000 data rows per import. This is a synchronous JSON API, not a large-file upload design.

## Reconciliation API

POST JSON to `/api/method/ledgerops.ledgerops.api.reconciliation.reconcile` with `bank_batch`, `ledger_batch`, and optional `date_window_days` (0–30).

The method proposes a match only when amount, currency and normalized non-empty reference match uniquely on both sides and the transaction dates fall inside the window. It creates exceptions for unmatched/ambiguous/difference/duplicate rows. Both batches move from Imported to Reconciled; rerunning the same batches is rejected.

## Current implementation boundaries

- Current DocType permissions are System Manager only. Build firm/staff/client RBAC and tenant isolation before pilot use.
- Evidence Request DocType exists; upload/download authorization and client portal are not yet implemented.
- No partial, many-to-many, opposite-sign, FX or fuzzy matching.
- No background import, retry/idempotency key, CSV mapping UI or large-file streaming.
- No live Frappe site was available in this work session; migration, DocType schema validation and Bench integration tests still require execution.
