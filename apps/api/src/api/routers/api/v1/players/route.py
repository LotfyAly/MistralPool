from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.elo import START_RATING
from db.accessors import players as players_db

router = APIRouter()


class PlayerIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class PlayerOut(BaseModel):
    id: int
    name: str
    rating: float
    wins: int
    losses: int
    draws: int
    rank: int


def _out(player, rank: int) -> PlayerOut:
    return PlayerOut(
        id=player.id,
        name=player.name,
        rating=player.rating,
        wins=player.wins,
        losses=player.losses,
        draws=player.draws,
        rank=rank,
    )


@router.get("", response_model=list[PlayerOut], operation_id="list_players", summary="Stand op rating")
async def list_players() -> list[PlayerOut]:
    players = await players_db.list_players()
    return [_out(p, i + 1) for i, p in enumerate(players)]


@router.post("", response_model=PlayerOut, status_code=201, operation_id="create_player", summary="Speler toevoegen")
async def create_player(body: PlayerIn) -> PlayerOut:
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Naam is verplicht")
    if await players_db.find_player_by_name(name) is not None:
        raise HTTPException(status_code=409, detail="Deze speler bestaat al")
    try:
        player = await players_db.create_player(name, START_RATING)
    except ValueError:
        raise HTTPException(status_code=409, detail="Deze speler bestaat al")
    players = await players_db.list_players()
    rank = next((i + 1 for i, p in enumerate(players) if p.id == player.id), len(players))
    return _out(player, rank)
