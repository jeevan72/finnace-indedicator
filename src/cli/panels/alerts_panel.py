from rich.table import Table
from rich.panel import Panel
from storage import models

def get_alerts_panel() -> Panel:
    """Generates the Rich panel streaming BSE Corporate Events & Hedging activities."""
    
    table = Table(show_header=False, expand=True, box=None)
    table.add_column("Timestamp", style="dim", width=12)
    table.add_column("Ticker", style="cyan", width=12)
    table.add_column("Type", style="bold yellow")
    table.add_column("Message")

    # Fetch 10 most recent corporate events
    events = models.Events.select().order_by(models.Events.timestamp.desc()).limit(10)
    for e in events:
        table.add_row(
            e.timestamp.strftime("%H:%M:%S") if hasattr(e.timestamp, 'strftime') else str(e.timestamp)[:8],
            e.symbol or "BSE",
            f"[{e.event_type.upper()}]",
            e.headline
        )
        
    if not list(events):
        table.add_row("-", "-", "INFO", "No corporate events flagged.")
        
    return Panel(table, title="Corporate Action Alerts", border_style="red")
