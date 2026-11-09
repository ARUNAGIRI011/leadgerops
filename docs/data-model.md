# Implemented initial data model

The current branch contains these Frappe DocTypes:

| DocType | Purpose | Main fields |
|---|---|---|
| LedgerOps Client | Client/customer master | name, email, phone, accounting system, status |
| LedgerOps Import Batch | Import provenance | client, source type, status, filename, SHA-256, row count |
| LedgerOps Bank Transaction | Staged bank row | batch, client, source row, date, description, reference, signed minor units, currency |
| LedgerOps Ledger Transaction | Staged ledger row | batch, client, source row, date, description, reference, signed minor units, currency |
| LedgerOps Match | Proposed reconciliation | bank row, ledger row, rule, confidence, status |
| LedgerOps Exception | Review work item | client, batch, linked transaction, type, title, status, priority, assignee, resolution note |
| LedgerOps Evidence Request | Evidence request record | client, exception, request text, due date, status, attachment field |
| LedgerOps Audit Event | Audit record | actor, action, referenced DocType/name, details |

## Security and tenancy boundary

At this stage all DocTypes are restricted to the Frappe System Manager role. This is intentionally restrictive and is not a customer-ready RBAC design. A single Frappe site should be treated as one firm boundary for the current pilot scaffold. Do not host multiple unrelated firms in one site until firm membership and server-side tenant filters are implemented and security-tested.

## Matching representation

Transaction amount is stored as integer minor units (e.g. paise). CSV credit values are positive and debit values are negative. Currency is an ISO-style three-letter alphabetic code validated by the importer. Confirm each source export's debit/credit convention before relying on matches.

The current schema uses an integer field for minor units. Its maximum numeric range must be validated against the deployed MariaDB/Frappe field mapping; if transactions can exceed that range, migrate to a decimal-safe or bigint representation before production.
