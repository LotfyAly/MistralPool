K_FACTOR = 32
START_RATING = 1200.0

SCORES = {"A": (1.0, 0.0), "B": (0.0, 1.0), "draw": (0.5, 0.5)}


def expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def elo_update(rating_a: float, rating_b: float, score_a: float) -> tuple[float, float]:
    score_b = 1.0 - score_a
    new_a = rating_a + K_FACTOR * (score_a - expected_score(rating_a, rating_b))
    new_b = rating_b + K_FACTOR * (score_b - expected_score(rating_b, rating_a))
    return round(new_a, 1), round(new_b, 1)
