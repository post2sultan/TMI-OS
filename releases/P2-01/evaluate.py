import json
import re
import sys
import time
from pathlib import Path

import httpx

from app.core.database import SessionLocal
from app.core.settings import settings
from app.models.campaign import Campaign
from app.services.analysis.document_builder import document_builder
from app.services.analysis.parser import analysis_parser
from app.services.analysis.prompt_builder import prompt_builder
from app.services.analysis.quality_validator import analysis_quality_validator
from app.services.scoring.engine import scoring_engine


CAMPAIGN_ID = 109
MODELS = ("qwen2.5:3b", "qwen2.5:7b")
RUNS_PER_MODEL = 2
MAX_TOTAL_RUNS = 4


def tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.casefold())
        if len(token) >= 4
    }


def generate(prompt: str, model: str) -> tuple[str, dict]:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "keep_alive": "10m",
        "options": {
            "temperature": 0,
            "num_predict": settings.AI_MAX_OUTPUT_TOKENS,
            "num_ctx": settings.AI_CONTEXT_WINDOW,
        },
    }
    with httpx.Client(timeout=900) as client:
        response = client.post(
            f"{settings.OLLAMA_URL.rstrip('/')}/api/generate",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
    if data.get("done") is not True:
        raise RuntimeError("Ollama generation did not complete.")
    if data.get("done_reason") == "length":
        raise RuntimeError("Ollama output reached its token ceiling.")
    return str(data.get("response") or ""), data


def loaded_model_metrics(model: str) -> dict:
    with httpx.Client(timeout=30) as client:
        response = client.get(
            f"{settings.OLLAMA_URL.rstrip('/')}/api/ps"
        )
        response.raise_for_status()
    record = next(
        (
            item
            for item in response.json().get("models", [])
            if item.get("name") == model
        ),
        {},
    )
    return {
        "loaded_size_gb": round(record.get("size", 0) / 1_000_000_000, 2),
        "vram_size_gb": round(
            record.get("size_vram", 0) / 1_000_000_000,
            2,
        ),
        "processor": (
            "GPU"
            if record.get("size_vram", 0) > 0
            else "CPU"
        ),
    }


def evaluate_run(campaign: Campaign, prompt: str, model: str) -> dict:
    started = time.perf_counter()
    raw = ""
    result = {
        "model": model,
        "json_compliant": False,
        "quality_passed": False,
        "dimension_complete": False,
        "evidence_url_accuracy": 0.0,
        "unsupported_evidence_token_rate": 1.0,
        "total_score": None,
        "confidence": None,
        "duration_seconds": None,
        "error": None,
    }
    try:
        raw, timing = generate(prompt, model)
        assessment = analysis_parser.parse(raw)
        result["json_compliant"] = True
        result["dimension_complete"] = len(assessment.dimensions) == 7
        quality = analysis_quality_validator.validate(
            assessment=assessment,
            campaign_context=(campaign.title,),
        )
        result["quality_passed"] = quality.is_valid
        if not quality.is_valid:
            result["error"] = "; ".join(quality.errors)

        evidence = [
            item
            for dimension in assessment.dimensions
            for item in dimension.evidence
        ]
        if evidence:
            correct_urls = sum(
                str(item.url).rstrip("/") == campaign.url.rstrip("/")
                for item in evidence
            )
            result["evidence_url_accuracy"] = round(
                correct_urls / len(evidence),
                4,
            )
            source_tokens = tokens(
                " ".join(
                    (
                        campaign.title,
                        campaign.description or "",
                        campaign.content or "",
                    )
                )
            )
            evidence_tokens = tokens(
                " ".join(item.description for item in evidence)
            )
            unsupported = evidence_tokens - source_tokens
            result["unsupported_evidence_token_rate"] = round(
                len(unsupported) / max(1, len(evidence_tokens)),
                4,
            )
        else:
            result["evidence_url_accuracy"] = 1.0
            result["unsupported_evidence_token_rate"] = 0.0

        scoring = scoring_engine.score(assessment)
        result["total_score"] = scoring.total_score
        result["confidence"] = scoring.confidence
        result["ollama_total_seconds"] = round(
            timing.get("total_duration", 0) / 1_000_000_000,
            2,
        )
        result["ollama_eval_tokens"] = timing.get("eval_count", 0)
    except Exception as error:
        result["error"] = str(error)[:1000]
    finally:
        result["duration_seconds"] = round(
            time.perf_counter() - started,
            2,
        )
        result.update(loaded_model_metrics(model))
    return result


def main() -> None:
    output = Path(sys.argv[1])
    output.parent.mkdir(parents=True, exist_ok=True)

    with SessionLocal() as database:
        campaign = database.get(Campaign, CAMPAIGN_ID)
        if campaign is None or not campaign.content:
            raise RuntimeError("Fixed evaluation campaign is unavailable.")
        prompt = prompt_builder.build(
            document_builder.build(campaign)
        ).content

        runs = []
        for model in MODELS:
            for run_number in range(1, RUNS_PER_MODEL + 1):
                if len(runs) >= MAX_TOTAL_RUNS:
                    raise RuntimeError("Evaluation run ceiling exceeded.")
                run = evaluate_run(campaign, prompt, model)
                run["run_number"] = run_number
                runs.append(run)

    summaries = {}
    for model in MODELS:
        model_runs = [run for run in runs if run["model"] == model]
        scores = [
            run["total_score"]
            for run in model_runs
            if run["total_score"] is not None
        ]
        summaries[model] = {
            "runs": len(model_runs),
            "valid_runs": sum(
                run["quality_passed"] for run in model_runs
            ),
            "average_duration_seconds": round(
                sum(run["duration_seconds"] for run in model_runs)
                / len(model_runs),
                2,
            ),
            "score_spread": (
                round(max(scores) - min(scores), 2)
                if len(scores) == len(model_runs)
                else None
            ),
            "average_evidence_url_accuracy": round(
                sum(
                    run["evidence_url_accuracy"]
                    for run in model_runs
                )
                / len(model_runs),
                4,
            ),
            "average_unsupported_evidence_token_rate": round(
                sum(
                    run["unsupported_evidence_token_rate"]
                    for run in model_runs
                )
                / len(model_runs),
                4,
            ),
        }

    payload = {
        "campaign_id": CAMPAIGN_ID,
        "models": list(MODELS),
        "runs_per_model": RUNS_PER_MODEL,
        "total_runs": len(runs),
        "paid_api_credits": 0,
        "production_model_changed": False,
        "runs": runs,
        "summaries": summaries,
    }
    output.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summaries))


if __name__ == "__main__":
    main()
