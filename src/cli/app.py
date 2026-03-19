import typer
from rich.console import Console

# Direct import works as sys.path appended in main.py
from cli.panels.prices_panel import get_prices_panel

app = typer.Typer(help="Financial Intelligence Terminal")
console = Console()

@app.command()
def prices():
    """Live prices panel (Section 13 layout)"""
    panel = get_prices_panel()
    console.print(panel)

@app.command()
def fetch_now(symbol: str = typer.Argument("Gold")):
    """Debug command to fetch a single price instantly via yfinance."""
    from fetchers.prices import fetch_price
    console.print(f"[yellow]Fetching {symbol} via yfinance...[/yellow]")
    res = fetch_price(symbol)
    if res:
        console.print("[green]Success![/green]", res)
    else:
        console.print("[red]Failed![/red]")

@app.command()
def dashboard():
    """Live dashboard aggregating all intelligence feeds (Section 13)"""
    from rich.layout import Layout
    from rich.live import Live
    from rich.console import Group
    
    from cli.panels.prices_panel import get_prices_panel
    from cli.panels.options_panel import get_options_panel
    from cli.panels.risk_panel import get_risk_panel
    from cli.panels.alerts_panel import get_alerts_panel
    
    # Define Layout
    layout = Layout()
    layout.split_row(
        Layout(name="left", ratio=4),
        Layout(name="center", ratio=3),
        Layout(name="right", ratio=3) # Changed from 2.5 to 3 because integer ratios are safer in Rich
    )
    
    # Left: Prices
    layout["left"].update(get_prices_panel())
    
    # Center: Options + Alerts
    layout["center"].split_column(
        Layout(get_options_panel()),
        Layout(get_alerts_panel())
    )
    
    # Right: Macro Risk + Trade Flows
    layout["right"].update(get_risk_panel())
    
    # Render
    # In a prod environment we'd use Live() for auto-refresh, but for phase 1 we just print once
    console.print(layout)

@app.command()
def daemon():
    """Starts the APScheduler Background Engine"""
    from scheduler.jobs import start_scheduler
    start_scheduler()
