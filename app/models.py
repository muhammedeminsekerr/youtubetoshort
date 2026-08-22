from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    youtube_url: str
    clip_count: int = Field(default=5, ge=1, le=10)
    min_duration: int = Field(default=20, ge=5, le=90)
    max_duration: int = Field(default=60, ge=10, le=180)
