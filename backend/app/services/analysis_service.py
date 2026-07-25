from app.services.prompt_service import prompt_service
from app.services.ollama_service import ollama_service


class AnalysisService:

    def analyse(self, user_prompt: str):

        system_prompt = prompt_service.load(
            "analysis",
            "campaign_analysis.md"
        )

        final_prompt = f"""
{system_prompt}

--------------------------------------------

USER REQUEST

{user_prompt}
"""

        response = ollama_service.generate(final_prompt)

        return response


analysis_service = AnalysisService()