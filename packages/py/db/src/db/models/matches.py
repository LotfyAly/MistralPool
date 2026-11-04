from datetime import datetime

from sqlmodel import Field, SQLModel

from .players import _utcnow


class Match(SQLModel, table=True):
    __tablename__ = "matches"

    id: int | None = Field(default=None, primary_key=True)
    player_a_id: int = Field(foreign_key="players.id")
    player_b_id: int = Field(foreign_key="players.id")
    result: str = Field(max_length=4)
    rating_a_before: float
    rating_b_before: float
    rating_a_after: float
    rating_b_after: float
    created_at: datetime = Field(default_factory=_utcnow)
