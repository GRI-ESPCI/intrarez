"""Intranet de la Rez Flask Web App - Run Entry Point"""

from typing import Any

from app import create_app, db, models, cli


app = create_app()
cli.register(app)


@app.shell_context_processor
def _make_shell_context() -> dict[str, Any]:
    """Define objects directly accessible in ``flask shell``."""
    return {"db": db, "models": models}
