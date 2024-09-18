from dataclasses import dataclass

import backoff
from chess import Board, Move
import requests


@dataclass
class MoveStats:
    move: Move
    white: int
    black: int
    draws: int

    @property
    def games(self) -> int:
        return self.white + self.black + self.draws

    @classmethod
    def from_lichess(cls, move):
        return cls(
            move=Move.from_uci(move["uci"]),
            white=move["white"],
            black=move["black"],
            draws=move["draws"],
        )


class LichessLimitReached(Exception):
    pass


class LichessAPI:
    def get(self, board: Board):
        fen = board.fen()
        response = self.fetch(fen)

        moves = [MoveStats.from_lichess(move) for move in response["moves"]]
        moves = sorted(moves, key=lambda move: move.games, reverse=True)

        return [move for move in moves]

    @backoff.on_exception(backoff.constant, LichessLimitReached, interval=60)
    def fetch(self, fen: str) -> dict:
        url = "https://explorer.lichess.ovh/lichess"
        query = {
            "speeds": "bullet,blitz,rapid,classical,correspondence",
            "ratings": "1600,1800,2000,2200,2500",
            "fen": fen,
            "topGames": 0,
            "recentGames": 0,
        }
        response = requests.get(url, query)

        if response.status_code == 429:
            raise LichessLimitReached()
        response.raise_for_status()

        return response.json()
