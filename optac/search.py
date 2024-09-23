import asyncio

from chess import Board
from chess.engine import EventLoopPolicy

from optac.analyse import Engine
from optac.explorer import LichessExplorer
from optac.params import OptacParams
from optac.position_store import PositionStore
from optac.tactic import Tactic
from optac.tactic_store import TacticStore


def mark_tactic_positions(tactic: Tactic, store: PositionStore):
    board = tactic.position.copy()
    board.push(tactic.solution[0])

    for ply, move in enumerate(tactic.solution[1:], start=1):
        with store.load(board) as position:
            position.tactic = tactic
            position.tactic_ply = ply
        board.push(move)


async def search(
    params: OptacParams,
    position_store: PositionStore,
    tactic_store: TacticStore,
):
    start = Board(params.start_fen)
    explorer = LichessExplorer(
        start_fen=params.start_fen,
        store=position_store,
        top_percent=params.search.top_percent,
        top_n=params.search.top_n,
        max_depth=params.search.max_depth,
        min_games=params.search.min_games,
    )

    engine = Engine(
        params.engine.exec,
        depth=params.engine.depth,
        options=params.engine.options,
    )

    with position_store:
        async with engine:
            for board in explorer:
                print(start.variation_san(board.move_stack), end="\t")

                with position_store.load(board) as position:
                    if position.in_tactic:
                        print("(*)", end="\t")
                        if position.starts_tactic:
                            tactic = print(str(position.tactic), end="\t")

                    else:
                        if position.analysis is None:
                            position.analysis = await engine.analyse(board)

                        if position.analysis is not None and position.tactic is None:
                            tactic = await Tactic.find_in_position(
                                position=board,
                                analysis=position.analysis,
                                engine=engine,
                            )

                            if tactic and (tactic.is_mate or tactic.wins_material):
                                position.tactic = tactic
                                position.tactic_ply = 0
                                mark_tactic_positions(tactic, position_store)

                                print("(new)\t" + str(tactic), end="")
                                tactic_store.store(tactic)
                print()


def run_search(
    params: OptacParams,
    position_store: PositionStore,
    tactic_store: TacticStore,
):
    asyncio.set_event_loop_policy(EventLoopPolicy())
    search_task = search(params, position_store, tactic_store)
    asyncio.run(search_task)
