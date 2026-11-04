from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.orm import aliased
from sqlmodel import select

from db.engine import get_session_maker
from db.models.matches import Match
from db.models.players import Player


@asynccontextmanager
async def write_session() -> AsyncIterator:
    async with get_session_maker()() as session:
        yield session


async def has_matches(player_id: int) -> bool:
    async with get_session_maker()() as session:
        result = await session.execute(
            select(Match.id).where((Match.player_a_id == player_id) | (Match.player_b_id == player_id)).limit(1)
        )
        return result.scalar_one_or_none() is not None


async def add_match(match: Match) -> Match:
    async with get_session_maker()() as session:
        session.add(match)
        await session.commit()
        await session.refresh(match)
        return match


async def list_matches(limit: int = 50) -> list[tuple[Match, str, str]]:
    a = aliased(Player)
    b = aliased(Player)
    async with get_session_maker()() as session:
        result = await session.execute(
            select(Match, a.name, b.name)
            .join(a, Match.player_a_id == a.id)
            .join(b, Match.player_b_id == b.id)
            .order_by(Match.id.desc())
            .limit(limit)
        )
        return [(m, name_a, name_b) for m, name_a, name_b in result.all()]
