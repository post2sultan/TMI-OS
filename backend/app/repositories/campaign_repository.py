from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.campaign import Campaign


class CampaignRepository:

    def save(self, campaign: Campaign):

        with SessionLocal() as db:

            db.add(campaign)

            db.commit()

            db.refresh(campaign)

            return campaign

    def find_by_url(self, url: str):

        with SessionLocal() as db:

            statement = (
                select(Campaign)
                .where(Campaign.url == url)
            )

            return db.scalar(statement)

    def find_all(self):

        with SessionLocal() as db:

            statement = (
                select(Campaign)
                .order_by(Campaign.id.desc())
            )

            return list(
                db.scalars(statement)
            )

    def update(self, campaign: Campaign):

        with SessionLocal() as db:

            db.merge(campaign)

            db.commit()

            db.refresh(campaign)

            return campaign

    def delete(self, campaign_id: int):

        with SessionLocal() as db:

            campaign = db.get(
                Campaign,
                campaign_id
            )

            if campaign:

                db.delete(campaign)

                db.commit()


campaign_repository = CampaignRepository()