import shelve
from dataclasses import dataclass
from pathlib import Path

from chess import Board

from optac.analyse import Analysis
from optac.lichess import MoveStats
from optac.tactic import Tactic


def fen_without_ply(board: Board) -> str:
    fen = board.fen()
    parts = fen.split(" ")
    assert len(parts) == 6
    return " ".join(parts[:4])


@dataclass
class Position:
    fen: str
    top_moves: list[MoveStats] | None = None
    analysis: Analysis | None = None
    tactic: Tactic | None = None
    tactic_ply: int = 0

    @property
    def starts_tactic(self):
        return self.in_tactic and self.tactic_ply == 0

    @property
    def in_tactic(self):
        return self.tactic is not None


class ActivePosition(Position):
    def __init__(self, position: Position, store: "PositionStore"):
        super().__init__(
            fen=position.fen,
            top_moves=position.top_moves,
            analysis=position.analysis,
            tactic=position.tactic,
            tactic_ply=position.tactic_ply,
        )

        self._store = store

    def __enter__(self):
        return self

    def __exit__(self, *args):
        position = Position(
            fen=self.fen,
            top_moves=self.top_moves,
            analysis=self.analysis,
            tactic=self.tactic,
            tactic_ply=self.tactic_ply,
        )
        self._store.commit(position)


class PositionStore:
    def __init__(self, path: Path):
        self.path = str(path)
        self.shelf: shelve.Shelf | None = None
        self.open_positions = set()

    def __enter__(self):
        self.shelf = shelve.open(self.path)
        return self

    def __exit__(self, *args):
        if self.shelf is not None:
            self.shelf.close()
            self.shelf = None

    def load(self, board: Board) -> ActivePosition:
        fen = fen_without_ply(board)

        if self.shelf is None:
            raise ValueError("PositionStore not open")

        if fen in self.open_positions:
            raise ValueError(f"Position already opened, {fen}")

        self.open_positions.add(fen)
        if fen in self.shelf:
            position = self.shelf[fen]
        else:
            position = Position(fen)

        return ActivePosition(position, self)

    def commit(self, position: Position):
        if self.shelf is None:
            raise ValueError("PositionStore not open")

        self.shelf[position.fen] = position
        self.open_positions.remove(position.fen)
