# GL-09 — Governed lifecycle completion

Implements and validates the operational workflow:

Discovery → Analyze → Review Queue → Approved → Published → Content Log

Approval now creates a durable content-creation job. Approved and Published
screens use lifecycle-specific backend queries. Publishing is an explicit,
audited action. The release includes database and image backups, schema
migration, automatic rollback, and a temporary-record end-to-end acceptance
test that cleans itself up.

Paid API credits: 0.
