# MistralPool — poolklassement als Mistral App

Webapp om het poolklassement tussen collega's bij te houden op Elo-basis (K=32, start 1200).
Gebouwd als [Mistral App](https://docs.mistral.ai/studio/apps/overview): FastAPI-backend + Postgres,
met een statische web-UI op `/`.

## Lokaal draaien

```bash
mistral dev
```

Start Docker eerst (lokale Postgres). Open daarna de geprinte URL.

## Deployen naar Mistral (Studio / Mistral Work)

```bash
mistral login
git push -u origin <branch>
mistral deploy          # bouwt de gepushte commit
mistral apps publish    # voegt de app toe aan de catalogus in Vibe/Mistral Work
```

De GitHub-repo moet via de [Mistral GitHub App](https://github.com/apps/mistralai) verbonden zijn.

## Structuur

- `apps/api` — FastAPI-module: routers onder `src/api/routers/api/v1`, Elo-logica in `src/api/elo.py`, statische UI in `static/`
- `packages/py/db` — SQLModel-modellen (`players`, `matches`), accessors en de Alembic-migratie
- `apps.json` — module/route-definitie; de api serveert `/api` én `/`

## API

- `GET /api/v1/players` — stand (gesorteerd op rating)
- `POST /api/v1/players` — `{name}`
- `DELETE /api/v1/players/{id}` — alleen zonder gespeelde wedstrijden
- `GET /api/v1/matches` — geschiedenis (nieuwste eerst)
- `POST /api/v1/matches` — `{a, b, result: "A"|"B"|"draw"}`
