# LedgerOps

**Reconciliation exceptions → client evidence → review → month-end close.**

LedgerOps is a Frappe-based workflow app for accounting and bookkeeping practices. It complements Tally, Zoho Books, QuickBooks, Xero and spreadsheet exports; it is not a general ledger, tax-filing engine or source of accounting truth.

> GitHub repository: `leadgerops` (spelled as created). Frappe/Python app: `ledgerops`.

## Implemented in this branch

- Frappe DocTypes: Client, Import Batch, Bank Transaction, Ledger Transaction, Match, Exception, Evidence Request and Audit Event.
- CSV parser with date/amount/currency validation, source-row numbers, 5 MiB payload cap and 10,000-row cap.
- CSV import API that records SHA-256 provenance and stages transactions.
- Deterministic one-to-one matching: exact signed amount in minor units + currency + normalized reference + date tolerance.
- Proposed matches and review exceptions for unmatched, ambiguous, amount/date differences and duplicate fingerprints.
- Audit event creation for imports and completed reconciliations.
- Pure-Python unit tests for normalization, matching and CSV parsing.

## API quick start

Create a client (authenticated Frappe API user):

```http
POST /api/resource/LedgerOps%20Client
Authorization: token <api_key>:<api_secret>
Content-Type: application/json

{"client_name":"Demo Client","accounting_system":"Excel","status":"Active"}
```

Import bank and ledger CSV content using POST JSON to:

`/api/method/ledgerops.ledgerops.api.imports.import_csv`

Request fields: `client`, `source_type` (`Bank Statement` or `Ledger Export`), `csv_text`, optional `source_filename`.

Example payload:

```json
{
  "client": "<client-document-name>",
  "source_type": "Bank Statement",
  "source_filename": "bank-october.csv",
  "csv_text": "transaction_date,description,reference,debit,credit,currency\n2026-10-01,Customer payment,UTR-001,0.00,1250.00,INR\n"
}
```

Call the same method with `source_type: "Ledger Export"` and the ledger CSV to create the second batch.

Then POST to `/api/method/ledgerops.ledgerops.api.reconciliation.reconcile`:

```json
{
  "bank_batch": "<bank-import-batch-name>",
  "ledger_batch": "<ledger-import-batch-name>",
  "date_window_days": 2
}
```

Frappe exposes DocType CRUD at `/api/resource/<DocType>` and whitelisted methods at `/api/method/<dotted.path>`. See the [Frappe REST API guide](https://docs.frappe.io/framework/user/en/api/rest).

## Important limitations

- Current DocType permissions are restricted to the Frappe **System Manager** role. This is a developer/pilot scaffold, not the final firm/staff/client RBAC model.
- The import endpoint accepts CSV text in a JSON request; it does not yet provide a browser upload UI or private File attachment workflow.
- Synchronous import/reconciliation is capped at 10,000 rows per batch. Larger jobs need background workers and idempotent chunk processing.
- Matching is deliberately conservative: no partial, one-to-many, many-to-many, FX, fuzzy or opposite-sign matching. Verify source accounting conventions before enabling automated matching.
- The evidence request DocType exists, but client portal, secure evidence upload/download, email delivery and reviewer approval workflow are not implemented yet.
- Tenant provisioning/isolation, production hardening, Frappe integration tests and deployment manifests remain open.
- This branch has not been installed against a live Frappe v16 site in this environment. Run the Bench migration and app tests before treating it as deployable.

## Development

Use a Frappe Bench with Frappe v16 and optional ERPNext on the same major branch:

```bash
bench get-app https://github.com/ARUNAGIRI011/leadgerops --branch bootstrap/ledgerops-mvp
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

Use synthetic data only during development. Keep API credentials server-side. Do not expose bank data, personal identifiers or evidence files publicly. The initial System Manager-only permissions are intentionally restrictive; implement and test tenant-aware roles before any customer pilot.

## Architecture and planning

- [Architecture](docs/architecture.md)
- [Data model](docs/data-model.md)
- [Security baseline](docs/security.md)
- [Product roadmap](docs/roadmap.md)
- [Development guide](docs/development.md)

## License

MIT for this custom app code. Frappe Framework and optional ERPNext retain their own licenses. Review dependency and distribution obligations before commercial distribution.
