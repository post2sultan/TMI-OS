import json

from app.schemas.campaign import Campaign
from app.services.analysis_service import analysis_service


class CampaignAnalyzer:

    def analyse(self, request: str) -> Campaign:

        response = analysis_service.analyse(request)

        response = self._clean_response(response)

        response = self._parse_json(response)

        campaign = Campaign(**response)

        return campaign

    def _clean_response(self, text: str):

        text = text.strip()

        if text.startswith("```json"):
            text = text.replace("```json", "", 1)

        if text.startswith("```"):
            text = text.replace("```", "", 1)

        if text.endswith("```"):
            text = text[:-3]

        return text.strip()

    def _parse_json(self, text: str):

        return json.loads(text)


campaign_analyzer = CampaignAnalyzer()