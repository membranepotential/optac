from pathlib import Path

import click

from optac.position_store import PositionStore
from optac.tactic_store import TacticStore
from optac.params import OptacParams
from optac.output import render_html
from optac.search import run_search


@click.group()
def cli():
    pass


@cli.command()
@click.argument("params", type=click.Path(exists=True))
@click.option(
    "--positions",
    "-c",
    type=click.Path(path_type=Path),
    default="positions.db",
)
@click.option("--puzzles", "-p", type=click.Path(path_type=Path), required=True)
def search(params, positions, puzzles):
    run_search(
        params=OptacParams.from_file(params),
        position_store=PositionStore(positions),
        tactic_store=TacticStore(puzzles),
    )


@cli.command()
@click.argument("path", type=click.Path(path_type=Path))
@click.option("--puzzles", "-p", type=click.Path(path_type=Path), required=True)
def render(path: Path, puzzles: Path):
    tactic_store = TacticStore(puzzles)
    tactics = tactic_store.list()

    html = render_html(tactics)
    path.write_text(html)


if __name__ == "__main__":
    cli()
