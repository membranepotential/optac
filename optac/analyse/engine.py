from contextlib import AbstractAsyncContextManager
from pathlib import Path

from chess import Board
from chess.engine import Limit, popen_uci, ConfigMapping

from .analysis import Analysis


class Engine(AbstractAsyncContextManager):
    def __init__(self, exec: Path, depth: int, options: ConfigMapping | None = None):
        self.exec = Path(exec)
        self.name = self.exec.name
        self.depth = depth

        if options is None:
            options = {}
        self.options = options

        self.transport = None
        self.engine = None

    async def spawn(self):
        self.transport, self.engine = await popen_uci(str(self.exec))

        # apply options one by one
        for key, value in self.options.items():
            if self.engine.options[key].is_managed():
                raise ValueError(f"Tried setting managed option: {key}")
            await self.engine.configure({key: value})

    async def close(self):
        if self.transport is not None:
            self.transport.close()
            self.transport = None

        if self.engine is not None:
            await self.engine.quit()
            self.engine = None

    async def analyse(self, board: Board) -> Analysis | None:
        if self.engine is None:
            raise ValueError("Engine not spawned")

        if board.is_game_over():
            return None

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
