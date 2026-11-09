# Development and test guide

## Prerequisites

- A supported Frappe Bench environment and compatible Python/Node/MariaDB/Redis versions.
- Frappe v16 branch for this initial target; optional ERPNext must use the same v16 branch.
- Exact OS/package versions depend on the official Frappe installation matrix; verify before provisioning.

## Install

```bash
bench get-app https://github.com/ARUNAGIRI011/leadgerops --branch bootstrap/ledgerops-mvp
bench --site <site-name> install-app ledgerops
bench --site <site-name> migrate
```

## Tests

Pure service tests can run with pytest when pytest is installed:

```bash
python -m pytest -q tests
```

Frappe app tests (once DocTypes and integration tests are added):

```bash
bench --site <site-name> run-tests --app ledgerops
```

## Current limitations

The bootstrap does not yet implement CSV upload/mapping, database DocTypes, role/permission fixtures, evidence upload APIs, tenant provisioning, Cloudflare adapter, or deployment manifests. Do not deploy this commit as a customer-facing production service.
