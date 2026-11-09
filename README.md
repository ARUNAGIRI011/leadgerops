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

## Public sales site and product-owner CRM

This branch adds an early-access sales and customer-operations layer alongside the reconciliation product.

### Public pages

- `/ledgerops` — product landing page with workflow positioning and demo-request form.
- `/privacy-policy` — early-access demo-request privacy notice template. It is not a complete legal privacy policy; the operating entity, contact, retention schedule, processors, transfer disclosures and applicable regional rights must be reviewed and completed before a public commercial launch.
- The public form collects contact/business details only. It explicitly tells visitors not to submit bank statements, tax identifiers or customer financial records.
- Guest endpoint: `POST /api/method/ledgerops.ledgerops.api.public_leads.submit_demo_request`.
- Basic controls: required business email/company/name, explicit contact consent, honeypot, bounded input lengths and server-side per-IP throttling. Reverse-proxy IP trust must be configured before relying on IP throttling behind a proxy.

### Internal CRM DocTypes

- `LedgerOps Lead`: lead source, pipeline stage, owner, estimated monthly value, team/client counts and consent metadata.
- `LedgerOps Account`: customer lifecycle, plan, MRR, renewal date and success owner.
- `LedgerOps Contact`: customer contacts and preferred contact channel.
- `LedgerOps CRM Activity`: calls, email, demos, meetings and tasks.
- `LedgerOps Subscription`: plan, status, billing interval, amount and current period end.
- `LedgerOps Support Case`: support queue, priority, category, assignment and resolution.

### Product-owner console

Desk route: `/app/ledgerops-owner`

The console reports:
- Leads, open leads, customers, active customers, subscriptions and open support cases.
- MRR grouped by currency (not combined across currencies).
- Open pipeline estimates grouped by currency (unweighted, not a forecast).
- Lead stages, recent leads and upcoming subscription periods.

Owner API: `GET /api/method/ledgerops.ledgerops.api.product_owner.get_overview`.

Customer list API: `GET /api/method/ledgerops.ledgerops.api.product_owner.list_customers`.

### CRM roles

- `LedgerOps Product Owner`: full CRM visibility and owner dashboard API.
- `LedgerOps Sales Manager`: lead/account/contact/activity/subscription/support visibility.
- `LedgerOps Sales Representative`: intentionally has no broad DocType access in the current permission setup. Do not assign this role in production until owner-scoped record permissions and cross-user access tests are implemented.
- `LedgerOps Customer Success`: accounts, contacts, activities, subscriptions and support cases.
- `LedgerOps Support Agent`: accounts, contacts and support cases.

CRM roles are separate from the accounting-workflow roles. They do not grant access to accounting transactions. The product-owner API is role-gated. Assign roles only to authorized internal staff.

### Important operating boundaries

- This CRM is an internal operator CRM for the LedgerOps SaaS owner; it is not the customer-facing accounting firm's client portal.
- Subscription records are operational records only. No payment gateway, invoicing, tax calculation, dunning or entitlement enforcement is implemented.
- MRR is derived from manually maintained customer account records and grouped by currency. It is not verified against a payment provider or accounting ledger.
- The landing page and demo form have not been tested on a live Frappe site.
- Before public launch, complete legal/privacy review, configure verified email delivery and CAPTCHA/WAF protection, test abuse controls behind the actual reverse proxy, and publish the real privacy contact.
- Add automated tests for lead capture, consent, duplicate updates, rate limits, CRM role access and dashboard aggregation before production.

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


## Production deployment runbook (Frappe Cloud)

This runbook describes a **staged release**, not a claim that LedgerOps is already production-ready. The repository branch must pass code review and CI, then be installed and tested on a separate staging site before a production site is changed.

### 1. Release prerequisites

Do not start a production rollout until all of the following are true:

- [ ] Review and merge the stacked pull requests in dependency order: PR #1, then PR #2, then PR #3. Rebase/update each dependent PR after its base is merged and resolve conflicts.
- [ ] Confirm the final release commit SHA and that the GitHub Actions checks for that commit completed successfully. A missing workflow run is **not** a passing check.
- [ ] Confirm the app installs and migrates on the exact Frappe v16 build selected for the bench. Check Frappe Cloud's current compatibility requirements before creating the bench.
- [ ] Complete the security and acceptance tests in the live-testing section below.
- [ ] Complete `/privacy-policy` with the real operating legal entity, privacy contact, purposes/legal basis, data categories, retention/deletion schedule, subprocessors, international transfers and applicable user rights. Obtain legal review for the countries in which the service will operate.
- [ ] Configure verified outbound email, abuse protection (CAPTCHA and/or WAF), reverse-proxy-aware rate limiting and monitoring.
- [ ] Confirm backup retention, off-site backup availability and a successful restore drill.
- [ ] Use synthetic data for staging. Do not use real bank statements, tax identifiers or customer financial records until the security and privacy controls have been approved.

**Release blocker:** one Frappe site per accounting firm is the supported initial tenancy boundary. Shared-site multi-tenant hosting is not implemented. Do not onboard multiple firms into one site.

### 2. Recommended Frappe Cloud layout

For the initial pilot, use Frappe Cloud with a **private bench group** (custom apps require a private bench) in the Mumbai region, and keep staging and production as separate sites. Select the smallest plan only for a low-volume pilot after checking current resource limits and pricing in the Frappe Cloud console; do not assume a starter plan is adequate for production load.

Suggested layout:

| Environment | Purpose | Data |
|---|---|---|
| Staging site | App install, migration, browser/API/security tests, release rehearsal | Synthetic fixtures only |
| Production site | Approved accounting firm pilot | Customer data only after sign-off |

Keep the same tested app commit and compatible Frappe major version in both environments. Do not test upgrades directly on production.

### 3. Create the private bench and connect the app

In Frappe Cloud (labels may change; follow the current console prompts):

1. Create or sign in to the Frappe Cloud account and configure billing/payment.
2. Create a **private bench group** in the selected region. Choose the supported Frappe v16 version and a compatible Python/runtime stack shown by Frappe Cloud.
3. Connect the GitHub organization/account and grant access only to the `ARUNAGIRI011/leadgerops` repository.
4. Add the custom app from the repository. For the first staging rehearsal, use the reviewed release branch/commit, not an unreviewed feature branch.
5. Deploy the bench version and wait for the build to complete successfully.
6. Create a staging site on that bench. Install `ledgerops` from the bench's app list if it is not already installed.
7. Record the bench version, app commit SHA, Frappe version, site URL and deployment timestamp in the release record.

Do not paste GitHub tokens, Frappe Cloud credentials, Cloudflare API tokens or site secrets into issues, commits, screenshots or this README.

### 4. Configure staging and production site settings

Set Cloudflare Workers AI settings on each site independently. Use the Frappe Cloud site's supported site-config interface or the bench command line where available:

```bash
bench --site <site-name> set-config cloudflare_workers_ai_account_id "<CLOUDFLARE_ACCOUNT_ID>"
bench --site <site-name> set-config cloudflare_workers_ai_api_token "<CLOUDFLARE_API_TOKEN>"
bench --site <site-name> set-config cloudflare_workers_ai_model "@cf/zai-org/glm-4.7-flash"
```

Use a dedicated, least-privilege token for Workers AI inference. Keep secrets out of source control and client-side JavaScript. Confirm the model is available to the Cloudflare account and that quota, billing, rate limits and data-processing terms are acceptable before enabling AI in production. AI assistance is optional; core reconciliation must remain usable if the AI provider is unavailable.

Also configure and verify:

- Site URL, HTTPS and trusted host/domain settings through Frappe Cloud.
- Email account/provider, sender domain authentication (SPF/DKIM/DMARC as applicable) and delivery tests.
- CAPTCHA/WAF rules and rate limits for the public demo endpoint.
- Reverse-proxy client-IP handling only for trusted proxy headers; never trust arbitrary client-supplied IP headers.
- Error logging, alerting, log retention and an operational support contact.
- Private file storage and file-size/type restrictions appropriate to the pilot.
- Backup schedule and retention, including off-site backups if offered by the selected plan.

### 5. Install, migrate and run tests (bench-managed environments)

For a self-managed bench, the basic commands are:

```bash
# Fetch the reviewed release branch (or the exact approved release tag)
bench get-app https://github.com/ARUNAGIRI011/leadgerops --branch <approved-release-branch>

# Install once on a new site
bench --site <site-name> install-app ledgerops

# Apply DocType/schema and patch migrations after an app update
bench --site <site-name> migrate

# Run the app's Frappe tests
bench --site <site-name> run-tests --app ledgerops

# Run the repository's pure-Python tests
python -m pip install pytest
python -m pytest -q tests
```

On Frappe Cloud, use its app/bench deployment workflow and site update controls; do not assume shell access is available on every plan. Do not run `install-app` again on a site where the app is already installed. Capture the full build, migration and test output. A successful bench build alone does not prove the app's workflows are correct.

### 6. Staging live-test checklist

Run these tests on the staging URL with separate test users and synthetic records. Record the test date, app commit SHA, tester, result and evidence for each case.

| Area | Test | Expected result |
|---|---|---|
| Install/migrate | Fresh site install, then repeat migrate | No install/migration exception; second migrate is safe/idempotent |
| Authentication | Open Desk and API routes as Guest and authenticated users | Guest cannot access private Desk/business data |
| Accounting roles | Test Admin, Manager, Accountant and Reviewer with separate users | Each role sees and performs only its documented actions |
| CRM owner API | Call product-owner overview/customer APIs as Product Owner and non-owner roles | Product Owner gets authorized response; unauthorized roles receive permission denial |
| Sales Representative | Attempt list, read, create, update and direct API access to CRM DocTypes | No broad CRM access is granted until owner-scoped permission hooks and tests exist |
| Public lead form | Submit valid details with explicit consent | Lead is created once and success response is shown |
| Public lead form | Omit consent, submit invalid email, exceed field limits, or fill honeypot | Request is rejected or safely ignored; no lead is created |
| Public lead form | Repeat requests from the same source through the real proxy | Throttling works; proxy/client IP cannot be spoofed |
| Duplicate lead | Submit same normalized business email repeatedly | Defined deduplication/update behavior; no uncontrolled duplicate records |
| CSV import | Valid CSV, malformed CSV, unsupported encoding, oversized payload and row-limit boundary | Valid data is staged; invalid/oversized input fails safely with useful errors |
| Reconciliation | Exact match, unmatched row, ambiguous match, duplicate fingerprint, amount/date/currency mismatch | Deterministic results; no silent false match |
| Evidence | Upload private file, register it against an exception, then try download as authorized and unauthorized users | Authorized user can access; unauthorized user cannot; private URL is not publicly readable |
| AI assist | Valid task, invalid task, missing token, provider timeout, quota/rate-limit response | Advisory text only; provider failure does not break core reconciliation or approve/post data |
| Dashboard | Load Desk dashboard and product-owner page with empty and populated data | No JS console errors; figures match fixture records; currencies remain separated |
| Browser | Test desktop and mobile widths on current Chrome/Firefox/Safari where supported | Forms, navigation and tables remain usable; no critical console/network errors |
| Backup/restore | Restore a recent staging backup to a separate test site | Site, app, private files and configuration recover as expected |

**Do not mark a row passed based only on a page loading.** Verify the underlying database state, API response, permissions and audit events where relevant.

### 7. Live API smoke tests

Use a staging site and a dedicated test account. Never put a real API key/secret in shell history, screenshots or CI logs. Frappe token authentication uses the form `Authorization: token <api_key>:<api_secret>`; obtain credentials securely from the site's user/API-key management flow.

Example read-only owner API request:

```bash
export LEDGEROPS_BASE_URL="https://<staging-host>"
read -r -p "Frappe API key: " FRAPPE_API_KEY
read -r -s -p "Frappe API secret: " FRAPPE_API_SECRET
echo

curl --fail-with-body --silent --show-error \
  -H "Authorization: token ${FRAPPE_API_KEY}:${FRAPPE_API_SECRET}" \
  -H "Accept: application/json" \
  "${LEDGEROPS_BASE_URL}/api/method/ledgerops.ledgerops.api.product_owner.get_overview"

unset FRAPPE_API_KEY FRAPPE_API_SECRET
```

Run the same request with a non-owner test user; it must be denied. Also test the public form endpoint with synthetic values only:

```bash
curl --fail-with-body --silent --show-error \
  -X POST "${LEDGEROPS_BASE_URL}/api/method/ledgerops.ledgerops.api.public_leads.submit_demo_request" \
  -H "Content-Type: application/json" \
  --data '{"name":"Staging Test","company":"Example Test Firm","email":"staging@example.invalid","consent":true}'
```

The public endpoint's exact accepted field names and response contract must be checked against the current implementation before using this example in automated tests. The reserved `.invalid` domain is for testing and cannot receive email. Do not send real personal data in smoke tests.

For exception AI assistance, use an existing synthetic exception and the documented endpoint:

```bash
curl --fail-with-body --silent --show-error \
  -X POST "${LEDGEROPS_BASE_URL}/api/method/ledgerops.ledgerops.api.ai.assist_exception" \
  -H "Authorization: token <TEST_API_KEY>:<TEST_API_SECRET>" \
  -H "Content-Type: application/json" \
  --data '{"exception_name":"<SYNTHETIC-EXCEPTION-ID>","task":"explain"}'
```

Confirm the response is advisory text and that no exception status, match, approval or accounting entry is changed by the AI request.

### 8. Production cutover

Only proceed after the release owner signs off the staging checklist.

1. Announce a short maintenance window and pause imports/user writes if this is an upgrade to an existing live site.
2. Take and verify a fresh pre-deployment backup, including private files and site configuration as supported by the platform.
3. Promote the exact app commit and bench version that passed staging. Do not deploy a moving feature branch.
4. Apply the Frappe Cloud site update/migration. Watch build and migration logs until completion.
5. Run a small read-only health check, authenticate as each production role, submit a synthetic demo request, and verify one controlled synthetic reconciliation if production policy permits.
6. Verify HTTPS/domain, email delivery, private evidence access, logs and alerts.
7. Re-enable normal writes/imports and onboard one pilot firm only after the release owner signs off.
8. Monitor error rates, queue/backlog, database/storage usage, AI quota and user-reported issues closely during the pilot.

### 9. Domain and HTTPS

Purchase the domain from a registrar when ready. In Frappe Cloud, add the domain to the intended production site and follow the exact DNS records displayed by the platform. Add the required A/AAAA/CNAME or verification records exactly as shown; do not copy guessed IP addresses or DNS targets from this README. Wait for DNS propagation and platform certificate issuance, then verify:

- HTTP redirects to HTTPS.
- The certificate hostname and validity are correct.
- The canonical hostname loads the landing page and Desk routes.
- The site does not expose staging or internal routes through the public domain.

The landing page currently lives at `/ledgerops`; configure a deliberate root-domain redirect or root route before advertising the bare domain.

### 10. Rollback and recovery

- If a code-only release fails before/without schema changes, redeploy the last known-good bench/app version using the Frappe Cloud deployment controls.
- If a migration changed the database schema or data, **do not assume that reverting code is a safe rollback**. Follow the platform's restore procedure and restore the matching database, private files and compatible app version from the pre-deployment backup.
- Validate the restored site on a separate URL before switching traffic back.
- Record the incident timeline, failed commit, migration output, backup identifier, restore result and customer impact.
- Never delete the only known-good backup during an incident.

### 11. Go-live acceptance record

A production release is accepted only when all items below are recorded as complete:

- [ ] Approved PRs merged in order and immutable release commit recorded.
- [ ] CI checks passed for the release commit.
- [ ] Fresh staging install and upgrade migration passed.
- [ ] Frappe app tests and pure-Python tests passed.
- [ ] Role/permission and cross-user evidence access tests passed.
- [ ] Public endpoint abuse, consent and proxy-rate-limit tests passed.
- [ ] Reconciliation correctness and import boundary tests passed.
- [ ] Backup restore drill passed.
- [ ] Privacy/legal, support, email and incident contacts approved.
- [ ] Production domain and HTTPS verified.
- [ ] Production smoke tests passed and release owner approved cutover.

**Current known status:** this README is a deployment and test runbook. It does not mean a Frappe Cloud bench/site has been provisioned, that the app has been installed on a live site, or that any live test has passed. Record actual environment details and test evidence in the release ticket; never mark unexecuted checks as passed.
