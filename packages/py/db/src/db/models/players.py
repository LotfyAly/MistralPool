from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Player(SQLModel, table=True):
    __tablename__ = "players"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=50, unique=True, index=True)
    rating: float = Field(default=1200.0)
    wins: int = Field(default=0)
    losses: int = Field(default=0)
    draws: int = Field(default=0)
    created_at: datetime = Field(default_factory=_utcnow)
