from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import json


@dataclass
class EngineParams:
    exec: Path
    depth: int
    options: dict = field(default_factory=dict)

    def __post_init__(self):
        self.exec = Path(self.exec)


@dataclass
class SearchParams:
    top_percent: Optional[int] = None
    top_n: Optional[int] = None
    max_depth: Optional[int] = None
    min_games: Optional[int] = None


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
