import json
import logging
import time

from app.core.settings import settings
from app.services.ai.base import AIProvider
from app.services.ai.cache import ai_cache
from app.services.ai.ollama_provider import ollama_provider
from app.services.ai.prompt_optimizer import prompt_optimizer


logger = logging.getLogger(__name__)


class AIRouter:

    def __init__(
        self,
        provider: AIProvider = ollama_provider,
    ) -> None:
        self.provider = provider

    @property
    def model(self) -> str:
        return settings.AI_PRIMARY_MODEL

    @property
    def embedding_model(self) -> str:
        return settings.OLLAMA_EMBEDDING_MODEL

    @staticmethod
    def _is_valid_json(
        response: str,
    ) -> bool:

        if not isinstance(response, str):
            return False

        response = response.strip()

        if not response:
            return False

        try:
            payload = json.loads(response)

        except json.JSONDecodeError:
            return False

        return isinstance(payload, dict)

    @staticmethod
    def _retry_max_output_tokens(
        initial_max_tokens: int,
        attempt: int,
    ) -> int:

        increased_max_tokens = (
            initial_max_tokens * (2 ** attempt)
        )

        return min(
            increased_max_tokens,
            settings.AI_CONTEXT_WINDOW,
        )

    def embed(
        self,
        text: str,
    ) -> list[float]:

        text = text.strip()

        if not text:
            raise ValueError(
                "Text cannot be empty."
            )

        return self.provider.embed(
            text=text,
            model=self.embedding_model,
        )

    def generate(
        self,
        prompt: str,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        require_json: bool = True,
    ) -> str:

        optimized_prompt = prompt_optimizer.optimize(
            prompt
        )

        if not optimized_prompt:
            raise ValueError(
                "Prompt cannot be empty."
            )

        selected_temperature = (
            temperature
            if temperature is not None
            else settings.AI_TEMPERATURE
        )

        initial_max_tokens = (
            max_output_tokens
            if max_output_tokens is not None
            else settings.AI_MAX_OUTPUT_TOKENS
        )

        last_error: Exception | None = None

        for model in settings.ai_models:

            for attempt in range(
                settings.AI_MAX_RETRIES + 1
            ):

                attempt_max_tokens = (
                    self._retry_max_output_tokens(
                        initial_max_tokens=(
                            initial_max_tokens
                        ),
                        attempt=attempt,
                    )
                )

                cached_response = ai_cache.get(
                    prompt=optimized_prompt,
                    model=model,
                    temperature=selected_temperature,
                    max_output_tokens=attempt_max_tokens,
                )

                if cached_response is not None:

                    if (
                        not require_json
                        or self._is_valid_json(
                            cached_response
                        )
                    ):
                        logger.info(
                            "AI cache hit",
                            extra={
                                "provider": (
                                    self.provider.name
                                ),
                                "model": model,
                                "attempt": attempt + 1,
                                "max_output_tokens": (
                                    attempt_max_tokens
                                ),
                            },
                        )

                        return cached_response

                    logger.warning(
                        "Ignoring invalid cached AI response",
                        extra={
                            "provider": self.provider.name,
                            "model": model,
                            "attempt": attempt + 1,
                            "max_output_tokens": (
                                attempt_max_tokens
                            ),
                        },
                    )

                started_at = time.perf_counter()

                try:

                    response = self.provider.generate(
                        prompt=optimized_prompt,
                        model=model,
                        temperature=selected_temperature,
                        max_output_tokens=(
                            attempt_max_tokens
                        ),
                    )

                    response_is_valid_json = (
                        self._is_valid_json(
                            response
                        )
                    )

                    if (
                        require_json
                        and not response_is_valid_json
                    ):
                        raise RuntimeError(
                            "AI provider returned incomplete "
                            "or invalid JSON."
                        )

                    duration_ms = round(
                        (
                            time.perf_counter()
                            - started_at
                        )
                        * 1000,
                        2,
                    )

                    if response_is_valid_json:
                        ai_cache.set(
                            prompt=optimized_prompt,
                            model=model,
                            temperature=selected_temperature,
                            max_output_tokens=(
                                attempt_max_tokens
                            ),
                            value=response,
                        )

                    logger.info(
                        "AI generation succeeded",
                        extra={
                            "provider": self.provider.name,
                            "model": model,
                            "attempt": attempt + 1,
                            "duration_ms": duration_ms,
                            "max_output_tokens": (
                                attempt_max_tokens
                            ),
                        },
                    )

                    return response

                except Exception as error:

                    last_error = error

                    logger.warning(
                        "AI generation failed",
                        extra={
                            "provider": self.provider.name,
                            "model": model,
                            "attempt": attempt + 1,
                            "max_output_tokens": (
                                attempt_max_tokens
                            ),
                            "error": str(error),
                        },
                    )

                    if attempt < settings.AI_MAX_RETRIES:
                        time.sleep(
                            settings.AI_RETRY_DELAY_SECONDS
                        )

        raise RuntimeError(
            f"All AI models and retries failed. Last error: {last_error}"
        ) from last_error


ai_router = AIRouter()
