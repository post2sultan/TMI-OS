from app.core.settings import settings


class PromptOptimizer:

    def optimize(
        self,
        prompt: str,
    ) -> str:
        normalized = "\n".join(
            line.rstrip()
            for line in prompt.strip().splitlines()
        )

        if len(normalized) <= settings.AI_PROMPT_MAX_CHARACTERS:
            return normalized

        return normalized[
            :settings.AI_PROMPT_MAX_CHARACTERS
        ]


prompt_optimizer = PromptOptimizer()