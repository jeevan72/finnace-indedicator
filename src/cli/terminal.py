import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import sys
import os

# Ensure src is in Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.models import Price
from fetchers.prices import fetch_all_prices
from storage.db import init_db
from utils.logger import get_logger

logger = get_logger(__name__)
app = typer.Typer()
console = Console()

def create_prices_table() -> Table:
    """Creates a Rich table for the latest prices from the DB."""
    table = Table(title="Live Market Prices (Phase 1)", show_header=True, header_style="bold magenta")
    table.add_column("Symbol", style="cyan")
    table.add_column("Price", justify="right")
    table.add_column("Change %", justify="right")
    table.add_column("Last Updated (UTC)", justify="right", style="dim")
    table.add_column("Source", justify="right", style="dim")

    # Fetch all, sort descending by time, get first per symbol
    query = Price.select().order_by(Price.timestamp.desc())
    latest_prices = {}
    
    for p in query:
        if p.symbol not in latest_prices:
            latest_prices[p.symbol] = p
            
    # Sort alphabetically
    for symbol in sorted(latest_prices.keys()):
        p = latest_prices[symbol]
        
        change_color = "green" if p.change_pct and p.change_pct >= 0 else "red"
        change_str = f"[{change_color}]{p.change_pct:.2f}%[/{change_color}]" if p.change_pct is not None else "N/A"
        price_str = f"{p.price:.4f}" if p.price is not None else "N/A"
        ts_str = p.timestamp.strftime("%Y-%m-%d %H:%M:%S") if p.timestamp else "N/A"
        
        table.add_row(symbol, price_str, change_str, ts_str, p.source or "Unknown")

    return table

@app.command()
def setup():
    """Initialize the database schema."""
    console.print("[yellow]Initializing database...[/yellow]")
    init_db()
    console.print("[green]Database initialized![/green]")

@app.command()
def fetch_prices():
    """Fetch latest prices and store in DB."""
    console.print("[yellow]Fetching latest prices from yFinance. This may take a moment...[/yellow]")
    fetch_all_prices()
    console.print("[green]Prices updated successfully![/green]")

@app.command()
def prices():
    """Display the prices panel."""
    table = create_prices_table()
    if table.row_count == 0:
        console.print("[red]No data found. Run 'prices-fetch' or similar command first.[/red]")
    else:
        console.print(Panel(table, expand=False, title="Market Summary"))

@app.command()
def refresh_prices():
    """Fetch prices and instantly display them."""
    fetch_prices()
    prices()

if __name__ == "__main__":
    app()
