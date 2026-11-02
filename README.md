# Poolklassement

Webapp om het poolklassement tussen collega's bij te houden op basis van Elo-rating.

## Starten

### Serverversie (gedeelde stand voor collega's)

```bash
python3 server.py
```

Open daarna http://127.0.0.1:8000 (poort instelbaar via `PORT`).

### Losstaand bestand (werkt zonder server)

Open `poolklassement.html` direct in een browser (dubbelklik). Data wordt in
`localStorage` van die browser bewaard.

## Functionaliteit

- Spelers toevoegen (start op 1200 Elo-punten) en verwijderen (alleen als er nog geen wedstrijden zijn)
- Wedstrijden registreren: winst links, winst rechts of gelijkspel
- Automatische Elo-berekening (K=32) met live update van de stand
- Wedstrijdgeschiedenis met ratingwijzigingen per speler
- Data wordt bewaard in `pool.db` (SQLite)

## Structuur

- `server.py` — backend (Python-standaardbibliotheek, geen externe packages)
- `static/index.html`, `static/style.css`, `static/app.js` — frontend
