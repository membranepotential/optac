from dataclasses import dataclass, field
from pathlib import Path
import json

from chess.engine import ConfigMapping


@dataclass
class EngineParams:
    exec: Path
    depth: int
    options: ConfigMapping = field(default_factory=dict)

    def __post_init__(self):
        self.exec = Path(self.exec)


@dataclass
class SearchParams:
    top_percent: int | None = None
    top_n: int | None = None
    max_depth: int | None = None
    min_games: int | None = None


@dataclass
class OptacParams:
    start_fen: str
    engine: EngineParams
    search: SearchParams

    @classmethod
    def from_file(cls, path: Path):
        with open(path) as f:
            params = json.load(f)

        return cls(
            params["start_fen"],
            EngineParams(**params["engine"]),
            SearchParams(**params["search"]),
        )
