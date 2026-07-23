"""LoopsBench CLI entry point."""

from dotenv import load_dotenv
from typer import Typer

from loopsbench.cli.runs import create, runs_app
from loopsbench.cli.tasks import tasks_app

load_dotenv()

app = Typer(
    name="loopsbench",
    no_args_is_help=True,
    help="LoopsBench: evaluate AI agents on long-horizon tasks.",
)
app.add_typer(tasks_app, name="tasks", help="Manage tasks.")
app.add_typer(runs_app, name="runs", help="Manage runs.")

# Shortcut: `loopsbench run ...` == `loopsbench runs create ...`
app.command(
    name="run",
    help="Run the LoopsBench harness (alias for `loopsbench runs create`).",
)(create)

if __name__ == "__main__":
    app()
