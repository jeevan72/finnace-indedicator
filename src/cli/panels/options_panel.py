from rich.table import Table
from rich.panel import Panel
from storage import models

def get_options_panel() -> Panel:
    """Generates a Rich panel containing the options snapshot intelligence."""
    # Group logically into a single table
    table = Table(show_header=True, header_style="bold blue", expand=True)
    table.add_column("Asset", style="cyan")
    table.add_column("Expiry", justify="center")
    table.add_column("PCR", justify="right")
    table.add_column("Max Pain", justify="right")
    table.add_column("ATM IV", justify="right")
    table.add_column("IV Rank", justify="right")
    
    # Fetch latest snapshot for each tracked options asset (e.g. NIFTY)
    query = models.OptionsSnapshot.select().order_by(models.OptionsSnapshot.timestamp.desc())
    latest_opts = {}
    for p in query:
        if p.symbol not in latest_opts:
            latest_opts[p.symbol] = p
            
    for symbol in sorted(latest_opts.keys()):
        p = latest_opts[symbol]
        
        # Color coding map
        pcr_color = "green" if p.pcr > 1.0 else "red" if p.pcr < 0.7 else "white"
        pcr_str = f"[{pcr_color}]{p.pcr:.2f}[/{pcr_color}]"
        
        iv_color = "red" if p.iv_rank > 80 else "green" if p.iv_rank < 30 else "white"
        iv_str = f"[{iv_color}]{p.iv_rank:.1f}[/{iv_color}]"
        
        table.add_row(
            p.symbol,
            str(p.expiry),
            pcr_str,
            f"{p.max_pain:.0f}",
            f"{p.atm_iv:.1f}%",
            iv_str
        )
        
    if not latest_opts:
        table.add_row("NIFTY", "Awaiting Data", "-", "-", "-", "-")
        
    return Panel(table, title="Derivatives Intelligence", border_style="magenta")
