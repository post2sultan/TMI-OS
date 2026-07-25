from app.models.campaign import Campaign

from app.repositories.campaign_repository import (
    campaign_repository,
)

from app.services.discovery.manager import (
    discovery_manager,
)

from app.services.extraction.manager import (
    extraction_manager,
)


class Pipeline:

    def discover_and_extract(
        self,
        query: str,
    ):

        campaigns = []

        discovered = discovery_manager.search(query)

        for item in discovered:

            existing = campaign_repository.find_by_url(
                item.url
            )

            if existing:

                campaigns.append(existing)

                continue

            extracted = extraction_manager.extract(
                item.url
            )

            if not extracted.success:

                continue

            campaign = Campaign(

                title=item.title,

                url=item.url,

                source=item.source,

                description=item.description,

                content=extracted.content,

            )

            saved_campaign = campaign_repository.save(
                campaign
            )

            campaigns.append(
                saved_campaign
            )

        return campaigns


pipeline = Pipeline()