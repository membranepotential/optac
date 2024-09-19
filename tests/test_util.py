import chess
from chess.engine import PovScore, Mate, Cp

from optac.util import score_to_dict, pov_score_from_dict


def test_mate_to_from_dict():
    score = PovScore(Mate(2), chess.BLACK)

    score_dict = score_to_dict(score)
    assert score_dict == {"mate": -2, "cp": None}

    parsed = pov_score_from_dict(score_dict, chess.BLACK)
    assert parsed.relative == Mate(2)
    assert parsed.turn == chess.BLACK


def test_cp_to_from_dict():
    score = PovScore(Cp(123), chess.BLACK)

    score_dict = score_to_dict(score)
    assert score_dict == {"mate": None, "cp": -123}

    parsed = pov_score_from_dict(score_dict, chess.BLACK)
    assert parsed.relative == Cp(123)
    assert parsed.turn == chess.BLACK
