import json
from pathlib import Path

from chess import Board

from optac.tactic import Tactic


class TacticStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.mkdir(exist_ok=True)

    @staticmethod
    def get_filename(tactic: Tactic):
        return "-".join(move.uci() for move in tactic.variation) + ".json"

    def store_root_board(self, root: Board):
        filename = self.path / "root.fen"
        with open(filename, "w") as f:
            f.write(root.fen())

    def store(self, tactic: Tactic):
        filename = self.path / self.get_filename(tactic)
        with open(filename, "w") as f:
            json.dump(tactic.as_dict(), f)

    def iter_tactics(self):
        for filename in self.path.iterdir():
            if filename.suffix != ".json":
                continue

            with open(filename) as f:
                tactic = Tactic.from_dict(json.load(f))
                yield tactic

    def list(self):
        return list(self.iter_tactics())
