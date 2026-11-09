# Security baseline

Before any customer data is accepted:

- Enforce firm membership and role checks in every read/write API and background job.
- Use separate sites/databases per firm for the initial deployment model.
- Require MFA for privileged accounts where supported; enforce strong session and password policies.
- HTTPS everywhere; restrict CORS; apply CSRF protections and rate limits.
- Store evidence privately; authorize each download; use short-lived signed URLs only if an object store is adopted.
- Encrypt backups and secrets; keep API tokens in server-side secret storage, never in browser code or Git.
- Record append-only audit events for import, matching, evidence, status and approval actions.
- Define retention, deletion, export, breach response and customer support access procedures.
- Test backup restoration and tenant isolation before launch.
- Use synthetic fixtures in development; mask bank references and personal identifiers in logs.
- Send only minimal masked context to an AI provider. Require human approval for generated messages and explanations.

Encryption alone does not establish DPDP/GDPR or other legal compliance. Obtain jurisdiction-specific legal/security review, DPAs, subprocessors list, retention terms and incident procedures before selling internationally.
