from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.elo import SCORES, elo_update
from db.accessors import matches as matches_db
from db.accessors import players as players_db
from db.models.matches import Match

router = APIRouter()


class MatchIn(BaseModel):
    a: int
    b: int
    result: str = Field(pattern="^(A|B|draw)$")


class RatingDelta(BaseModel):
    before: float
    after: float


class MatchOut(BaseModel):
    id: int
    name_a: str
    name_b: str
    result: str
    rating_a: RatingDelta
    rating_b: RatingDelta
    created_at: str


class RecordedMatch(BaseModel):
    match: MatchOut


async def _match_out(match: Match, name_a: str, name_b: str) -> MatchOut:
    return MatchOut(
        id=match.id,
        name_a=name_a,
        name_b=name_b,
        result=match.result,
        rating_a=RatingDelta(before=match.rating_a_before, after=match.rating_a_after),
        rating_b=RatingDelta(before=match.rating_b_before, after=match.rating_b_after),
        created_at=match.created_at.isoformat(),
    )


@router.get("", response_model=list[MatchOut], operation_id="list_matches", summary="Wedstrijdgeschiedenis")
async def list_matches(limit: int = 50) -> list[MatchOut]:
    rows = await matches_db.list_matches(min(limit, 200))
    return [await _match_out(m, a, b) for m, a, b in rows]


@router.post("", response_model=RecordedMatch, status_code=201, operation_id="record_match", summary="Wedstrijd registreren")
async def record_match(body: MatchIn) -> RecordedMatch:
    if body.a == body.b:
        raise HTTPException(status_code=400, detail="Kies twee verschillende spelers")
    player_a = await players_db.get_player(body.a)
    player_b = await players_db.get_player(body.b)
    if player_a is None or player_b is None:
        raise HTTPException(status_code=404, detail="Speler niet gevonden")

    score_a, _ = SCORES[body.result]
    a_before, b_before = player_a.rating, player_b.rating
    a_after, b_after = elo_update(a_before, b_before, score_a)

    match = Match(
        player_a_id=player_a.id,
        player_b_id=player_b.id,
        result=body.result,
        rating_a_before=a_before,
        rating_b_before=b_before,
        rating_a_after=a_after,
        rating_b_after=b_after,
    )

    player_a.rating = a_after
    player_b.rating = b_after
    if body.result == "A":
        player_a.wins += 1
        player_b.losses += 1
    elif body.result == "B":
        player_b.wins += 1
        player_a.losses += 1
    else:
        player_a.draws += 1
        player_b.draws += 1

    async with matches_db.write_session() as session:
        session.add(match)
        session.add(player_a)
        session.add(player_b)
        await session.commit()
        await session.refresh(match)

    return RecordedMatch(match=await _match_out(match, player_a.name, player_b.name))
