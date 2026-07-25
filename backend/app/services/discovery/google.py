from duckduckgo_search import DDGS

from app.models.campaign_source import CampaignSource


class GoogleDiscovery:

    MAX_RESULTS = 5

    def discover(self, company: str):

        query = (
            f"{company} marketing campaign "
            f"OR advertising campaign "
            f"OR digital campaign "
            f"OR brand campaign"
        )

        campaigns = []

        with DDGS() as ddgs:

            results = ddgs.text(
                keywords=query,
                max_results=self.MAX_RESULTS
            )

            for result in results:

                campaigns.append(
                    CampaignSource(
                        title=result.get("title", ""),
                        url=result.get("href", ""),
                        source="DuckDuckGo",
                        description=result.get("body", ""),
                        content=""
                    )
                )

        return campaigns


google_discovery = GoogleDiscovery()