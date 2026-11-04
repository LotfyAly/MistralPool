from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from db.engine import get_session_maker
from db.models.players import Player


async def list_players() -> list[Player]:
    async with get_session_maker()() as session:
        result = await session.execute(select(Player).order_by(Player.rating.desc(), Player.name))
        return list(result.scalars().all())


async def get_player(player_id: int) -> Player | None:
    async with get_session_maker()() as session:
        return await session.get(Player, player_id)


async def find_player_by_name(name: str) -> Player | None:
    async with get_session_maker()() as session:
        result = await session.execute(select(Player).where(Player.name.ilike(name)))
        return result.scalars().first()


async def create_player(name: str, rating: float) -> Player:
    player = Player(name=name, rating=rating)
    async with get_session_maker()() as session:
        session.add(player)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise ValueError("name-taken")
        await session.refresh(player)
        return player


async def save_player(player: Player) -> None:
    async with get_session_maker()() as session:
        session.add(player)
        await session.commit()


async def delete_player(player_id: int) -> bool:
    async with get_session_maker()() as session:
        player = await session.get(Player, player_id)
        if player is None:
            return False
        await session.delete(player)
        await session.commit()
        return True
