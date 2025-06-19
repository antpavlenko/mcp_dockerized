import typer
from server import init_db, create_api_key

app = typer.Typer(help="MCP server management")

@app.command()
def init_db_command():
    """Initialize the database."""
    init_db()
    typer.echo("Database initialized")

@app.command()
def generate_key():
    """Generate a new API key."""
    init_db()
    key = create_api_key()
    typer.echo(key)

if __name__ == "__main__":
    app()
