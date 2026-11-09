# Initial data model

Planned Frappe DocTypes (the list is design intent; DocType schemas and permission matrices are not yet implemented):

| DocType | Purpose | Key fields |
|---|---|---|
| LedgerOps Firm | Tenant / practice | firm name, status, external tenant key |
| LedgerOps Client | Customer entity | firm, display name, contact, accounting system |
| LedgerOps Engagement | Period of work | firm, client, period start/end, status |
| LedgerOps Import Batch | Source provenance | firm, client, source type, file, checksum, status, counts |
| LedgerOps Bank Transaction | Imported bank row | batch, source row, date, amount_minor, currency, reference |
| LedgerOps Ledger Transaction | Imported ledger row | batch, source row, date, amount_minor, currency, reference |
| LedgerOps Match | Proposed/confirmed relation | bank row, ledger row, rule, reviewer, status |
| LedgerOps Exception | Work item | type, severity, status, owner, due date, match candidates |
| LedgerOps Evidence Request | Client request | exception, requested items, due date, status |
| LedgerOps Evidence | Private file metadata | request, exception, file, uploaded by, checksum |
| LedgerOps Audit Event | Append-only history | actor, action, target, timestamp, reason |

All tenant-owned records must have a server-enforced firm relationship. Never trust a client-supplied firm identifier without checking the authenticated user's membership. Do not expose private evidence files through public URLs.
