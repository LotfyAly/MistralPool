"""De app-routes voor het poolklassement, served for an ingelogde caller via de gateway."""

from fastapi import HTTPException, params
from mistralai_capabilities.apps.tokens import current_token

segment = "v1"


async def require_caller() -> None:
    if current_token() is None:
        raise HTTPException(status_code=401, detail="Inloggen verplicht")


dependencies: tuple[params.Depends, ...] = (params.Depends(require_caller),)
