# TMI OS P0-03 — Analysis Run Records

Persists an independent audit record for every analysis generation attempt.

Each record stores:

- campaign ID;
- model and prompt version;
- attempt number;
- raw response;
- passed, failed, or error status;
- validation or provider error;
- start and completion timestamps;
- duration in milliseconds; and
- force flag.

Attempt records commit independently, so failed generations remain inspectable even when the analysis transaction rolls back. The release includes the `analysis_runs` migration and a reversible downgrade.
