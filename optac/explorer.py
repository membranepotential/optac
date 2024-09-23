from collections import deque
from typing import Iterator

from chess import Board, Move

from optac.lichess import LichessAPI, MoveStats
from optac.position_store import PositionStore


class LichessExplorer:
    def __init__(
        self,
        start_fen: str,
        store: PositionStore,
        max_depth: int | None = None,
        min_games: int | None = None,
        top_percent: int | None = None,
        top_n: int | None = None,
    ):
        self.start = start_fen
        self.store = store

        self.max_depth = max_depth
        self.min_games = min_games
        self.top_percent = top_percent
        self.top_n = top_n
        assert top_percent or top_n, "top_percent or top_n must be set"

        self.lichess = LichessAPI()

    def filter_top_moves(self, moves: list[MoveStats]) -> Iterator[Move]:
        if self.top_percent is not None:
            total = sum(move.games for move in moves)
            cumulative = 0.0

        if self.top_n is not None:
            moves = moves[: self.top_n]

        for move in moves:
            if self.min_games is not None:
                if move.games < self.min_games:
                    return

            yield move.move

            if self.top_percent is not None:
                cumulative += move.games / total
                if cumulative > self.top_percent / 100:
                    return

    def __iter__(self) -> Iterator[Board]:
        return self.search_moves()

    def search_moves(self) -> Iterator[Board]:
        queue = deque([Board(self.start)])
        while queue:
            board = queue.popleft()
            yield board

            if self.max_depth is not None and len(board.move_stack) < self.max_depth:
                next_moves = []

                with self.store.load(board) as position:
                    if position.in_tactic:
                        forced_move = position.tactic.solution[position.tactic_ply]
                        next_moves.append(forced_move)
                    else:
                        if not position.top_moves:
                            position.top_moves = self.lichess.get(board)
                        next_moves.extend(self.filter_top_moves(position.top_moves))

                for move in next_moves:
                    next_board = board.copy()
                    next_board.push(move)
                    queue.append(next_board)
