from fastapi import APIRouter, HTTPException

from db.accessors import matches as matches_db
from db.accessors import players as players_db

router = APIRouter()


@router.delete("", operation_id="delete_player", summary="Speler verwijderen (alleen zonder wedstrijden)")
async def delete_player(player_id: int) -> dict[str, int]:
    if await players_db.get_player(player_id) is None:
        raise HTTPException(status_code=404, detail="Speler niet gevonden")
    if await matches_db.has_matches(player_id):
        raise HTTPException(
            status_code=409, detail="Speler kan niet verwijderd worden: er zijn al wedstrijden gespeeld"
        )
    await players_db.delete_player(player_id)
    return {"deleted": player_id}
