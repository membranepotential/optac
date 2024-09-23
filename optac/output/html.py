from pathlib import Path

import chess
from chess.svg import board as render_svg
from jinja2 import Environment, FileSystemLoader

from optac.tactic import Tactic


def render_pgn(tactic: Tactic):
    pgn = '[Variant "From Position"]\n'
    pgn += f'[FEN "{tactic.variation_start.fen()}"]\n\n'
    pgn += tactic.variation_san(with_solution=True)
    return pgn


def prepare_puzzles(tactics: list[Tactic]):
    puzzles = []
    for tactic in tactics:
        if len(tactic.solution) < 2:
            continue

        lastmove = tactic.position.move_stack[-1]
        diagram = render_svg(
            tactic.position,
            orientation=tactic.color,
            lastmove=lastmove,
        )
        puzzle = {
            "svg": diagram,
            "color": "white" if tactic.color == chess.WHITE else "black",
            "fen": tactic.position.fen(),
            "variation_san": tactic.variation_san(),
            "solution_san": tactic.solution_san(),
            "pgn": render_pgn(tactic),
            "ply": tactic.position.ply(),
        }
        puzzles.append(puzzle)

    # sort by color
    puzzles.sort(key=lambda p: p["color"])

    # add puzzle number
    puzzles = [{"index": i + 1, **p} for i, p in enumerate(puzzles)]

    return puzzles


def render_html(tactics: list[Tactic]) -> str:
    puzzles = prepare_puzzles(tactics)

    jinja = Environment(
        loader=FileSystemLoader(Path(__file__).parent),
        autoescape=False,
    )
    template = jinja.get_template("template.html")
    return template.render(puzzles=puzzles)
