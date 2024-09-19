import pytest
from chess import Board, Move

from optac.analyse import Engine
from optac.tactic import Tactic

ITALIAN = "r2qkbnr/ppp2ppp/2np4/4p2b/2B1P3/2N2N1P/PPPP1PP1/R1BQK2R w KQkq - 1 6"


@pytest.fixture
def italian() -> Board:
    board = Board(ITALIAN)
    board.push_san("Nxe5")
    board.push_san("Bxd1")
    return board


@pytest.fixture(scope="function")
async def engine():
    async with Engine("/usr/bin/stockfish", depth=15) as engine:
        yield engine


async def test_mate(engine: Engine, italian: Board):
    analysis = await engine.analyse(italian)
    assert analysis is not None

    tactic = await Tactic.find_in_position(italian, analysis, engine)

    assert tactic is not None
    assert tactic.is_mate
    assert tactic.variation_san
    assert tactic.solution_san

    assert tactic.as_dict() == {
        "variation_start": ITALIAN,
        "variation": ["f3e5", "h5d1"],
        "score": {"mate": 2, "cp": None},
        "solution": ["c4f7", "e8e7", "c3d5"],
    }

    tactic = Tactic.from_dict(tactic.as_dict())
    assert tactic.position.fen() == italian.fen()
    assert tactic.position.move_stack == [Move.from_uci("f3e5"), Move.from_uci("h5d1")]
    assert tactic.solution == [
        Move.from_uci("c4f7"),
        Move.from_uci("e8e7"),
        Move.from_uci("c3d5"),
    ]

    assert tactic.is_mate
    assert tactic.variation_san
    assert tactic.solution_san
