from pydantic import BaseModel


class Evidence(BaseModel):
    source: str
    title: str
    content: str
    confidence: float = 1.0