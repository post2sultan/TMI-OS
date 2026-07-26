from typing import Any
from uuid import UUID

from qdrant_client import QdrantClient, models

from app.core.settings import settings


class QdrantService:
    """Manage campaign vectors in Qdrant."""

    def __init__(self) -> None:
        self.collection_name = settings.QDRANT_COLLECTION_NAME

        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=(
                settings.QDRANT_API_KEY.get_secret_value()
                or None
            ),
            timeout=settings.QDRANT_TIMEOUT_SECONDS,
        )

    @staticmethod
    def _distance() -> models.Distance:
        distances = {
            "cosine": models.Distance.COSINE,
            "dot": models.Distance.DOT,
            "euclid": models.Distance.EUCLID,
        }

        return distances[settings.QDRANT_DISTANCE]

    def ensure_collection(self) -> None:
        if self.client.collection_exists(self.collection_name):
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=settings.QDRANT_VECTOR_SIZE,
                distance=self._distance(),
            ),
        )

    def store_vector(
        self,
        point_id: str | int | UUID,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None:
        self.ensure_collection()

        if len(vector) != settings.QDRANT_VECTOR_SIZE:
            raise ValueError(
                f"Expected vector size {settings.QDRANT_VECTOR_SIZE}, "
                f"received {len(vector)}."
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            ],
            wait=True,
        )

    def get_vector(
        self,
        point_id: str | int | UUID,
    ) -> dict[str, Any] | None:
        self.ensure_collection()

        records = self.client.retrieve(
            collection_name=self.collection_name,
            ids=[point_id],
            with_payload=True,
            with_vectors=True,
        )

        if not records:
            return None

        record = records[0]

        return {
            "id": record.id,
            "vector": record.vector,
            "payload": record.payload or {},
        }

    def search_similar(
        self,
        vector: list[float],
        limit: int = 5,
        score_threshold: float | None = None,
        query_filter: models.Filter | None = None,
    ) -> list[dict[str, Any]]:
        self.ensure_collection()

        if len(vector) != settings.QDRANT_VECTOR_SIZE:
            raise ValueError(
                f"Expected vector size {settings.QDRANT_VECTOR_SIZE}, "
                f"received {len(vector)}."
            )

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True,
            with_vectors=False,
        )

        return [
            {
                "id": point.id,
                "score": point.score,
                "payload": point.payload or {},
            }
            for point in response.points
        ]

    def health_check(self) -> dict[str, Any]:
        self.ensure_collection()

        collection = self.client.get_collection(
            collection_name=self.collection_name
        )

        return {
            "status": "healthy",
            "collection": self.collection_name,
            "vector_size": settings.QDRANT_VECTOR_SIZE,
            "distance": settings.QDRANT_DISTANCE,
            "points_count": collection.points_count or 0,
        }


qdrant_service = QdrantService()
