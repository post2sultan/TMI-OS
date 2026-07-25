ALTER TABLE analyses
    ADD COLUMN IF NOT EXISTS review_status VARCHAR(30)
        NOT NULL DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(255),
    ADD COLUMN IF NOT EXISTS review_reason TEXT,
    ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;

ALTER TABLE campaigns
    ADD COLUMN IF NOT EXISTS status VARCHAR(30)
        NOT NULL DEFAULT 'discovered';

CREATE INDEX IF NOT EXISTS ix_analyses_review_status
    ON analyses (review_status);

CREATE INDEX IF NOT EXISTS ix_campaigns_status
    ON campaigns (status);