"""Intranet de la Rez Flask Web App - Run Entry Point"""

from app import create_app, db, models, cli

app = create_app()
cli.register(app)

@app.shell_context_processor
def make_shell_context():
    """Define objects directly accessible in ``flask shell``."""
    return {"db": db, "models": models}
