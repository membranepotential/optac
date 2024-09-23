from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import chess
import pytest
from chess import Board, Move
from chess.engine import Cp, PovScore

from optac.analyse import Analysis, ScoredPV
from optac.lichess import MoveStats
from optac.position_store import PositionStore, fen_without_ply


@pytest.fixture(scope="session")
def tmpdir():
    with TemporaryDirectory() as dirname:
        yield Path(dirname)


@pytest.fixture
def position_store(tmpdir):
    with PositionStore(tmpdir / str(uuid4())) as store:
        yield store


@pytest.fixture
def top_moves():
    return [MoveStats(Move.from_uci("e2e4"), 1, 2, 3)]


@pytest.fixture
def analysis() -> Analysis:
    move = Move.from_uci("e7e5")
    score = PovScore(Cp(10), chess.WHITE)
    result = ScoredPV([move], score)
    return Analysis(
        "stockfish",
        depth=20,
        result=[result],
    )


def test_position_store(position_store, top_moves, analysis):
    board = Board()
    with position_store.load(board) as position:
        assert position.top_moves is None
        assert position.analysis is None
        assert position.tactic is None
        assert position.tactic_parent_fen is None

        position.top_moves = top_moves
        position.analysis = analysis

    with position_store.load(board) as position:
        assert position.top_moves == top_moves
        assert position.analysis == analysis
        assert position.tactic is None
        assert position.tactic_parent_fen is None


def test_mark_tactic(position_store):
    tactic_start = Board()
    board = Board()
    board.push_san("e4")

    with position_store.load(board) as position:
        assert not position.dont_explore
        position.mark_tactic(tactic_start)

    with position_store.load(board) as position:
        assert position.tactic_parent_fen == fen_without_ply(tactic_start)
        assert position.dont_explore


def test_transposition(position_store, top_moves):
    board1 = Board()
    for san in "e4 e5 Nf3 Nc6".split():
        board1.push_san(san)

    board2 = Board()
    for san in "Nf3 Nc6 e4 e5".split():
        board2.push_san(san)

    with position_store.load(board1) as position:
        assert position.top_moves is None
        position.top_moves = top_moves

    with position_store.load(board2) as position:
        assert position.top_moves == top_moves
