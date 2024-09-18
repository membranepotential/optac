from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


from chess import Board, Move
from chess.engine import popen_uci, Limit, PovScore

from optac.util import (
    score_to_dict,
    pov_score_from_dict,
    color_as_string,
    color_from_string,
)


@dataclass
class Analysis:
    engine: str
    depth: int
    best: list[Move]
    best_score: Optional[PovScore]
    alternate: list[Move]
    alt_score: Optional[PovScore]

    @classmethod
    def game_over(cls):
        return cls(
            engine="", depth=0, best=[], alternate=[], best_score=None, alt_score=None
        )

    @classmethod
    def from_engine(cls, engine_name: str, depth: int, result: dict):
        if len(result) > 0:
            best = result[0]["pv"]
            best_score = result[0]["score"]
        else:
            best = []
            best_score = None

        if len(result) > 1:
            alternate = result[1]["pv"]
            alt_score = result[1]["score"]
        else:
            alternate = []
            alt_score = None

        return cls(
            engine=engine_name,
            depth=depth,
            best=best,
            alternate=alternate,
            best_score=best_score,
            alt_score=alt_score,
        )

    @classmethod
    def from_dict(cls, analysis_dict: dict):
        if not analysis_dict["best"]:
            return cls.game_over()

        color = color_from_string(analysis_dict["color"])

        return cls(
            engine=analysis_dict["engine"],
            depth=analysis_dict["depth"],
            best=[Move.from_uci(move) for move in analysis_dict["best"]],
            alternate=[Move.from_uci(move) for move in analysis_dict["alternate"]],
            best_score=pov_score_from_dict(analysis_dict["best_score"], color),
            alt_score=pov_score_from_dict(analysis_dict["alt_score"], color),
        )

    @property
    def only_move(self):
        return self.best and not self.alternate

    @property
    def best_move(self):
        return self.best[0] if self.best else None

    @property
    def force(self):
        if self.is_mate or self.only_move:
            return float("inf")

        best_score = self.best_score.relative.score(mate_score=float("inf"))
        alt_score = self.alt_score.relative.score(mate_score=float("inf"))
        return best_score - alt_score

    def is_forced(self, threshold: int) -> bool:
        return not self.is_game_over and self.force > threshold

    @property
    def is_mate(self):
        return self.best_score and self.best_score.is_mate()

    @property
    def is_game_over(self):
        return not self.best

    @property
    def evaluation(self):
        return self.best_score

    @property
    def color(self):
        if self.is_game_over:
            return None
        else:
            return self.best_score.turn

    def as_dict(self):
        return {
            "engine": self.engine,
            "depth": self.depth,
            "best": [move.uci() for move in self.best],
            "alternate": [move.uci() for move in self.alternate],
            "best_score": score_to_dict(self.best_score),
            "alt_score": score_to_dict(self.alt_score),
            "color": color_as_string(self.color),
        }


class Engine(AbstractAsyncContextManager):
    def __init__(self, exec: Path, depth: int, options: Optional[dict] = None):
        self.exec = Path(exec)
        self.name = self.exec.name
        self.depth = depth

        if options is None:
            options = {}
        self.options = options

        self.transport = None
        self.engine = None

    async def spawn(self):
        self.transport, self.engine = await popen_uci(self.exec)

        # apply options one by one
        for key, value in self.options.items():
            if self.engine.options[key].is_managed():
                raise ValueError(f"Tried setting managed option: {key}")
            await self.engine.configure({key: value})

    async def close(self):
        self.transport.close()
        await self.engine.quit()

    async def analyse(self, board: Board):
        if self.engine is None:
            raise ValueError("Engine not spawned")

        if board.is_game_over():
            return Analysis.game_over()

        result = await self.engine.analyse(
            board,
            limit=Limit(depth=self.depth),
            multipv=2,
        )
        return Analysis.from_engine(
            engine_name=self.name,
            depth=self.depth,
            result=result,
        )

    async def __aenter__(self):
        await self.spawn()
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.close()
