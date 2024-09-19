from dataclasses import dataclass

from chess import Color, Move
from chess.engine import InfoDict, PovScore

from optac.util import (
    color_as_string,
    color_from_string,
    pov_score_from_dict,
    score_to_dict,
)


@dataclass
class ScoredPV:
    pv: list[Move]
    score: PovScore

    @property
    def turn(self):
        return self.score.turn

    @classmethod
    def from_result(cls, result: InfoDict):
        try:
            return cls(
                pv=result["pv"],
                score=result["score"],
            )
        except KeyError:
            raise ValueError("Result is missing PV or score")

    @classmethod
    def from_dict(cls, pv_dict: dict, turn: Color):
        return cls(
            pv=[Move.from_uci(move) for move in pv_dict["pv"]],
            score=pov_score_from_dict(pv_dict["score"], turn),
        )

    def as_dict(self):
        return {
            "pv": [move.uci() for move in self.pv],
            "score": score_to_dict(self.score),
        }

    def __getitem__(self, index):
        return self.pv[index]

    def __iter__(self):
        return iter(self.pv)


@dataclass
class Analysis:
    engine: str
    depth: int
    result: list[ScoredPV]

    @property
    def best(self) -> ScoredPV:
        if not self.result:
            raise ValueError("Analysis has no PVs")
        return self.result[0]

    @property
    def alternate(self) -> ScoredPV | None:
        if len(self.result) < 2:
            return None
        return self.result[1]

    @property
    def only_move(self):
        return self.best and self.alternate is None

    @property
    def best_move(self):
        return self.best[0]

    @property
    def is_mate(self):
        if not self.result:
            return True
        return self.best.score.is_mate()

    @property
    def evaluation(self):
        return self.best.score

    @property
    def turn(self):
        return self.best.turn

    @property
    def force(self):
        if self.is_mate or self.only_move:
            return float("inf")

        assert self.alternate is not None

        best_score = self.best.score.relative.score()
        alt_score = self.alternate.score.relative.score()

        if best_score is None or alt_score is None:
            return float("inf")

        return best_score - alt_score

    def is_forced(self, threshold: int) -> bool:
        return self.force > threshold

    @classmethod
    def from_engine(cls, engine_name: str, depth: int, result: list[InfoDict]):
        return cls(
            engine=engine_name,
            depth=depth,
            result=[ScoredPV.from_result(r) for r in result],
        )

    @classmethod
    def from_dict(cls, analysis_dict: dict):
        turn = color_from_string(analysis_dict["turn"])
        return cls(
            engine=analysis_dict["engine"],
            depth=analysis_dict["depth"],
            result=[ScoredPV.from_dict(pv, turn) for pv in analysis_dict["result"]],
        )

    def as_dict(self):
        return {
            "engine": self.engine,
            "depth": self.depth,
            "result": [result.as_dict() for result in self.result],
            "turn": color_as_string(self.turn),
        }
