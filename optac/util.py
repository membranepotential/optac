import chess
from chess.engine import Cp, Mate, PovScore, Score


def score_to_dict(score: Score | PovScore) -> dict[str, int | None]:
    if isinstance(score, PovScore):
        score = score.white()

    if score.is_mate():
        return {"mate": score.mate(), "cp": None}
    else:
        return {"mate": None, "cp": score.score()}


def score_from_dict(score_dict: dict[str, int | None]) -> Score:
    if score_dict["mate"]:
        return Mate(score_dict["mate"])
    else:
        assert score_dict["cp"] is not None
        return Cp(score_dict["cp"])


def pov_score_from_dict(
    score_dict: dict[str, int | None],
    color: chess.Color = chess.WHITE,
) -> PovScore:
    score = score_from_dict(score_dict)

    if color != chess.WHITE:
        score = -score

    return PovScore(score, turn=color)


def color_as_string(color: chess.Color) -> str:
    return "white" if color == chess.WHITE else "black"


def color_from_string(color: str) -> chess.Color:
    return chess.WHITE if color == "white" else chess.BLACK
