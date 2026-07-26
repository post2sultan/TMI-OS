# TMI OS Production Backlog

Last updated: 2026-07-25

## Current Production Baseline

- Backend API operational
- PostgreSQL operational
- Redis operational
- Qdrant operational
- SearXNG operational
- Ollama operational
- Campaign discovery operational
- Campaign analysis operational
- Seven-dimension scoring operational
- Evidence objects operational
- Analysis persistence operational
- Vector storage operational
- Forced re-analysis operational
- Current model: qwen2.5:3b

---

## NOW — Production Foundation

### P0-01 Analysis Quality Validation

Add deterministic validation to reject placeholder or template-copy output.

Reject an analysis when:

- Every dimension has the same score
- Every dimension has identical reasoning
- Evidence descriptions match template placeholders
- Summary matches an automatic fallback phrase
- Strengths, weaknesses and recommendations are all empty
- The analysis contains no campaign-specific language

Expected result:

- Invalid analysis is not saved
- API returns a clear validation error
- Failed output is logged for inspection

Status: Complete

---

### P0-02 Analysis Retry

Automatically retry once when the first LLM response:

- Is invalid JSON
- Fails Pydantic validation
- Fails analysis-quality validation
- Returns only one dimension
- Copies the response template

Expected result:

- First attempt remains strict
- Second attempt receives concise correction instructions
- Only validated output is persisted

Status: Complete

---

### P0-03 Analysis Run Records

Persist every analysis attempt separately from successful analyses.

Store:

- Campaign ID
- Model name
- Prompt version
- Attempt number
- Raw response
- Validation status
- Error message
- Started timestamp
- Completed timestamp
- Duration
- Force flag

Expected result:

- Full audit trail
- Failed generations remain inspectable
- Production debugging does not depend on Docker logs

Status: Complete

---

### P0-04 Remove Temporary Debug Output

Remove temporary console debugging after analysis-run records are operational.

Remove:

- DEBUG force print
- Raw response console dump
- Temporary traceback formatting

Retain:

- Structured application logging
- Error-level exception logging
- Analysis attempt records

Status: Next

---

## NEXT — Campaign Evidence Pipeline

### P1-01 Campaign Source Documents

Support multiple source documents per campaign.

Document types:

- Web page
- News article
- Press release
- Social post
- Video page
- Image
- Uploaded document
- Manual observation

Status: Backlog

---

### P1-02 Evidence Extraction

Extract structured evidence from campaign sources.

Store:

- Source URL
- Source type
- Title
- Extracted text
- Published date
- Retrieved date
- Language
- Brand
- Campaign
- Media assets
- Extraction status

Status: Backlog

---

### P1-03 Evidence Deduplication

Prevent duplicate campaign documents and repeated source content.

Use:

- Canonical URL
- Content hash
- Semantic similarity
- Campaign association

Status: Backlog

---

### P1-04 Evidence Confidence

Assign confidence and provenance to extracted evidence.

Store:

- Evidence origin
- Extraction method
- Confidence
- Direct quote or paraphrase
- Supporting source
- Retrieval timestamp

Status: Backlog

---

## NEXT — Campaign Workflow

### P1-05 Campaign Status Lifecycle

Implement campaign statuses:

- discovered
- shortlisted
- researching
- ready_for_analysis
- analyzing
- analyzed
- needs_review
- approved
- rejected
- published
- archived

Status: Backlog

---

### P1-06 Campaign Review API

Create endpoints to:

- List campaigns awaiting review
- Read campaign evidence
- Read latest analysis
- Approve analysis
- Reject analysis
- Edit analysis
- Trigger re-analysis
- Archive campaign

Status: Backlog

---

### P1-07 Analysis Versioning

Never overwrite a previous analysis.

Store:

- Analysis version
- Previous analysis ID
- Prompt version
- Model version
- Constitution version
- Approval status
- Reviewer notes

Status: Backlog

---

## LATER — Model Upgrade

### P2-01 Local Model Evaluation

Evaluate stronger models against a fixed TMI test set.

Candidate models:

- qwen2.5:7b
- qwen2.5:14b
- qwen3:8b
- qwen3:14b
- llama3.1:8b

Measure:

- JSON compliance
- Dimension completeness
- Campaign-specific reasoning
- Evidence accuracy
- Hallucination rate
- Analysis duration
- RAM usage
- CPU usage
- Output consistency

Status: Deferred

---

### P2-02 Model Migration

Replace qwen2.5:3b only after evaluation.

Requirements:

- Model configurable through environment variables
- No model name hardcoded in application services
- Existing analysis records retain original model metadata
- Health check verifies model availability
- Startup does not silently switch models
- Migration documented
- Rollback supported

Status: Deferred

---

### P2-03 External Model Provider Support

Add a provider-independent AI interface supporting:

- Ollama
- OpenAI-compatible APIs
- Future hosted inference providers

Status: Deferred

---

## LATER — Retrieval and Intelligence

### P2-04 Constitution Retrieval

Retrieve only the relevant constitution sections for each dimension.

Status: Deferred

---

### P2-05 Similar Campaign Retrieval

Use Qdrant to retrieve:

- Similar campaign sources
- Comparable analyses
- Category benchmarks
- Historical campaign patterns

Status: Deferred

---

### P2-06 Analysis Comparison

Compare campaigns by:

- Total score
- Dimension score
- Confidence
- Brand
- Category
- Market
- Date
- Campaign objective

Status: Deferred

---

## LATER — Publishing

### P3-01 Script Generation

Generate approved campaign-review scripts.

Status: Deferred

---

### P3-02 Social Copy Generation

Generate platform-specific copy for:

- YouTube
- Instagram
- TikTok
- X

Status: Deferred

---

### P3-03 Voice Generation

Generate review narration after approval.

Status: Deferred

---

### P3-04 Video Assembly

Create review videos and reels from approved content.

Status: Deferred

---

### P3-05 Publishing Approval

Require explicit approval before publishing.

Status: Deferred

---

## Production Rules

1. Complete file replacements only.
2. One production task at a time.
3. Validate every change before proceeding.
4. No successful analysis may be overwritten.
5. No invalid LLM output may be persisted.
6. Every generated result must retain model and prompt provenance.
7. Human approval is mandatory before public publishing.
8. Deferred work must remain recorded in this backlog.
