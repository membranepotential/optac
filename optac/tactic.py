from dataclasses import dataclass

import chess
from chess import Board, Move
from chess.engine import PovScore

from optac.analyse import Analysis, Engine
from optac.util import score_to_dict, pov_score_from_dict

PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,
}


@dataclass
class Tactic:
    position: Board
    score: PovScore
    solution: list[Move]

    @property
    def color(self):
        return self.position.turn

    @property
    def is_mate(self):
        return self.score.is_mate()

    @property
    def wins_material(self):
        balance = 0
        board = self.position.copy()
        for move in self.solution:
            captured = board.piece_at(move.to_square)
            if captured is not None:
                value = PIECE_VALUES[captured.piece_type]
                if captured.color == self.color:
                    balance -= value
                else:
                    balance += value
            board.push(move)

        return balance > 0

    @property
    def variation(self):
        return self.position.move_stack

    @property
    def variation_start(self):
        start = self.position.copy()
        while start.move_stack:
            start.pop()
        return start

    def variation_san(self, with_solution: bool = False):
        board = self.variation_start
        moves = self.position.move_stack

        if with_solution:
            moves += self.solution

        return board.variation_san(moves)

    def solution_san(self):
        return self.position.variation_san(self.solution)

    @staticmethod
    async def calculate_forced_sequence(
        board: Board,
        analysis: Analysis | None,
        engine: Engine,
        threshold: int = 100,
    ):
        if board.is_game_over() or analysis is None:
            raise ValueError("Cannot calculate finished game")

        board = board.copy(stack=False)
        last_score = analysis.evaluation
        forced_sequence = []
        continue_sequence = True

        while continue_sequence:
            forced_sequence.append(analysis.best_move)
            last_score = analysis.evaluation

            board.push(analysis.best_move)

            analysis = await engine.analyse(board)
            if analysis is None:
                # Game over
                break

            continue_sequence = (
                analysis.is_forced(threshold)
                or board.is_capture(analysis.best_move)
                or board.is_into_check(analysis.best_move)
            )

        return forced_sequence, last_score

    @classmethod
    async def find_in_position(
        cls,
        position: Board,
        analysis: Analysis,
        engine: Engine,
        threshold: int = 100,
    ):
        if analysis.is_mate:
            return cls(
                position=position.copy(),
                score=analysis.evaluation,
                solution=analysis.best.pv,
            )

        elif analysis.is_forced(threshold):
            forced_sequence, score = await cls.calculate_forced_sequence(
                board=position,
                analysis=analysis,
                engine=engine,
                threshold=threshold,
            )

            return cls(
                position=position.copy(),
                score=score,
                solution=forced_sequence,
            )

        return None

    def __str__(self):
        return str(self.score) + " " + self.solution_san()

    def as_dict(self):
        return {
            "variation_start": self.variation_start.fen(),
            "variation": [move.uci() for move in self.variation],
            "score": score_to_dict(self.score),
            "solution": [move.uci() for move in self.solution],
        }

    @classmethod
    def from_dict(cls, data: dict):
        position = Board(data["variation_start"])
        for uci in data["variation"]:
            position.push_uci(uci)

        return cls(
            position=position,
            score=pov_score_from_dict(data["score"], position.turn),
            solution=[Move.from_uci(uci) for uci in data["solution"]],
        )
