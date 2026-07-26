# TMI OS P1-05 — Campaign Status Lifecycle

Adds the complete controlled campaign lifecycle from discovery through
publication and archival.

Invalid status jumps are rejected, analysis automatically enters and exits its
processing states, failures return campaigns to `ready_for_analysis`, and
existing approval, rejection, and reanalysis actions use the same transition
rules. PostgreSQL enforces the allowed status set.
