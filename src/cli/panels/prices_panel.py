from rich.table import Table
from rich.panel import Panel
from storage.models import Prices
from utils.time_utils import format_ist_display

def _format_inr(value: float) -> str:
    """Formats a number in Indian numbering system (e.g. 1,78,250.00)."""
    int_part = int(value)
    dec_part = f"{value - int_part:.2f}"[1:]  # .XX
    s = str(int_part)
    if len(s) <= 3:
        return s + dec_part
    # Last 3 digits, then groups of 2
    result = s[-3:]
    s = s[:-3]
    while s:
        result = s[-2:] + "," + result
        s = s[:-2]
    return result + dec_part

def get_prices_panel() -> Panel:
    """Generates a Rich panel containing the prices table."""
    table = Table(show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Asset", style="cyan")
    table.add_column("Price", justify="right")
    table.add_column("Change %", justify="right")
    table.add_column("52W H/L", justify="center")
    table.add_column("Source", justify="center", style="dim")
    table.add_column("Time (IST)", justify="right", style="dim")
    
    # SQLite does not easily do distinct-on. Pulling all and grabbing first manually.
    query = Prices.select().order_by(Prices.timestamp.desc())
    latest_prices = {}
    for p in query:
        if p.symbol not in latest_prices:
            latest_prices[p.symbol] = p
            
    for symbol in sorted(latest_prices.keys()):
        p = latest_prices[symbol]
        
        if p.change_pct > 0:
            change_color = "green"
        elif p.change_pct < 0:
            change_color = "red"
        else:
            change_color = "white"
            
        change_str = f"[{change_color}]{p.change_pct:+.2f}%[/{change_color}]"
        
        # Format with [D] prefix if delayed per specs
        asset_str = f"[dim yellow]\\[D][/dim yellow] {p.name}" if p.is_delayed else p.name
        
        high_low = "N/A" # Not collected in Phase 1 prices fetcher
        
        time_str = format_ist_display(p.timestamp)
        
        # Format price with currency symbol
        currency = getattr(p, 'currency', 'INR')
        if currency == "INR":
            price_str = f"₹{_format_inr(p.price)}"
        else:
            price_str = f"${p.price:,.4f}"
        
        table.add_row(
            asset_str,
            price_str,
            change_str,
            high_low,
            p.source,
            time_str
        )
        
    return Panel(table, title="Prices & India VIX", border_style="blue")
