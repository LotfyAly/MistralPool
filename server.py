import json
import math
import os
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DB_PATH = os.path.join(BASE_DIR, "pool.db")

K_FACTOR = 32
START_RATING = 1200.0

lock = threading.Lock()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                rating REAL NOT NULL DEFAULT 1200,
                wins INTEGER NOT NULL DEFAULT 0,
                losses INTEGER NOT NULL DEFAULT 0,
                draws INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_a_id INTEGER NOT NULL REFERENCES players(id),
                player_b_id INTEGER NOT NULL REFERENCES players(id),
                result TEXT NOT NULL CHECK (result IN ('A', 'B', 'draw')),
                rating_a_before REAL NOT NULL,
                rating_b_before REAL NOT NULL,
                rating_a_after REAL NOT NULL,
                rating_b_after REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


def expected_score(ra, rb):
    return 1.0 / (1.0 + 10.0 ** ((rb - ra) / 400.0))


def elo_update(ra, rb, score_a):
    score_b = 1.0 - score_a
    new_a = ra + K_FACTOR * (score_a - expected_score(ra, rb))
    new_b = rb + K_FACTOR * (score_b - expected_score(rb, ra))
    return round(new_a, 1), round(new_b, 1)


SCORES = {"A": (1.0, 0.0), "B": (0.0, 1.0), "draw": (0.5, 0.5)}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status=400):
        self.send_json({"error": message}, status)

    def read_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/standings":
            self.handle_standings()
        elif path == "/api/matches":
            self.handle_matches()
        elif path.startswith("/api/players"):
            self.handle_standings()
        else:
            self.serve_static(path)

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/players":
            self.handle_add_player()
        elif path == "/api/matches":
            self.handle_add_match()
        else:
            self.send_error_json("Onbekend pad", 404)

    def do_DELETE(self):
        path = urlparse(self.path).path
        if path.startswith("/api/players/"):
            try:
                player_id = int(path.rsplit("/", 1)[1])
            except ValueError:
                self.send_error_json("Ongeldig id", 400)
                return
            self.handle_delete_player(player_id)
        else:
            self.send_error_json("Onbekend pad", 404)

    def handle_standings(self):
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT id, name, rating, wins, losses, draws,
                       wins + losses + draws AS games
                FROM players
                ORDER BY rating DESC, name COLLATE NOCASE
                """
            ).fetchall()
        standings = [dict(r) for r in rows]
        for i, p in enumerate(standings, start=1):
            p["rank"] = i
        self.send_json({"players": standings})

    def handle_matches(self):
        query = parse_qs(urlparse(self.path).query)
        limit = min(int(query.get("limit", [50])[0]), 200)
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT m.id, m.result, m.rating_a_before, m.rating_b_before,
                       m.rating_a_after, m.rating_b_after, m.created_at,
                       a.name AS name_a, b.name AS name_b
                FROM matches m
                JOIN players a ON a.id = m.player_a_id
                JOIN players b ON b.id = m.player_b_id
                ORDER BY m.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        self.send_json({"matches": [dict(r) for r in rows]})

    def handle_add_player(self):
        data = self.read_body()
        if data is None:
            self.send_error_json("Ongeldige JSON", 400)
            return
        name = str(data.get("name", "")).strip()
        if not name:
            self.send_error_json("Naam is verplicht", 400)
            return
        if len(name) > 50:
            self.send_error_json("Naam mag maximaal 50 tekens zijn", 400)
            return
        with lock, get_db() as conn:
            existing = conn.execute(
                "SELECT id FROM players WHERE name = ? COLLATE NOCASE", (name,)
            ).fetchone()
            if existing:
                self.send_error_json("Deze speler bestaat al", 409)
                return
            cur = conn.execute(
                "INSERT INTO players (name, rating) VALUES (?, ?)",
                (name, START_RATING),
            )
            player_id = cur.lastrowid
        self.send_json({"id": player_id, "name": name, "rating": START_RATING}, 201)

    def handle_delete_player(self, player_id):
        with lock, get_db() as conn:
            has_matches = conn.execute(
                "SELECT 1 FROM matches WHERE player_a_id = ? OR player_b_id = ? LIMIT 1",
                (player_id, player_id),
            ).fetchone()
            if has_matches:
                self.send_error_json(
                    "Speler kan niet verwijderd worden: er zijn al wedstrijden gespeeld", 409
                )
                return
            cur = conn.execute("DELETE FROM players WHERE id = ?", (player_id,))
            if cur.rowcount == 0:
                self.send_error_json("Speler niet gevonden", 404)
                return
        self.send_json({"deleted": player_id})

    def handle_add_match(self):
        data = self.read_body()
        if data is None:
            self.send_error_json("Ongeldige JSON", 400)
            return
        try:
            a_id = int(data.get("a"))
            b_id = int(data.get("b"))
        except (TypeError, ValueError):
            self.send_error_json("Spelers ontbreken", 400)
            return
        result = str(data.get("result", "")).strip()
        if a_id == b_id:
            self.send_error_json("Kies twee verschillende spelers", 400)
            return
        if result not in SCORES:
            self.send_error_json("Resultaat moet 'A', 'B' of 'draw' zijn", 400)
            return
        score_a, score_b = SCORES[result]
        with lock, get_db() as conn:
            a = conn.execute(
                "SELECT id, name, rating, wins, losses, draws FROM players WHERE id = ?", (a_id,)
            ).fetchone()
            b = conn.execute(
                "SELECT id, name, rating, wins, losses, draws FROM players WHERE id = ?", (b_id,)
            ).fetchone()
            if a is None or b is None:
                self.send_error_json("Speler niet gevonden", 404)
                return
            ra, rb = a["rating"], b["rating"]
            new_a, new_b = elo_update(ra, rb, score_a)
            conn.execute(
                """
                INSERT INTO matches (player_a_id, player_b_id, result,
                    rating_a_before, rating_b_before, rating_a_after, rating_b_after)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (a_id, b_id, result, ra, rb, new_a, new_b),
            )
            if result == "A":
                conn.execute(
                    "UPDATE players SET rating = ?, wins = wins + 1 WHERE id = ?", (new_a, a_id)
                )
                conn.execute(
                    "UPDATE players SET rating = ?, losses = losses + 1 WHERE id = ?", (new_b, b_id)
                )
            elif result == "B":
                conn.execute(
                    "UPDATE players SET rating = ?, losses = losses + 1 WHERE id = ?", (new_a, a_id)
                )
                conn.execute(
                    "UPDATE players SET rating = ?, wins = wins + 1 WHERE id = ?", (new_b, b_id)
                )
            else:
                conn.execute(
                    "UPDATE players SET rating = ?, draws = draws + 1 WHERE id = ?", (new_a, a_id)
                )
                conn.execute(
                    "UPDATE players SET rating = ?, draws = draws + 1 WHERE id = ?", (new_b, b_id)
                )
        self.send_json(
            {
                "match": {
                    "a": a["name"],
                    "b": b["name"],
                    "result": result,
                    "rating_a": {"before": ra, "after": new_a},
                    "rating_b": {"before": rb, "after": new_b},
                }
            },
            201,
        )

    def serve_static(self, path):
        if path in ("/", ""):
            path = "/index.html"
        safe = os.path.normpath(path).lstrip("/")
        full = os.path.join(STATIC_DIR, safe)
        if not full.startswith(STATIC_DIR) or not os.path.isfile(full):
            self.send_error_json("Niet gevonden", 404)
            return
        content_types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".ico": "image/x-icon",
        }
        ext = os.path.splitext(full)[1].lower()
        with open(full, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_types.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    init_db()
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Poolklassement draait op http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
