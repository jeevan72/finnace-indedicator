from rich.table import Table
from rich.panel import Panel
from rich.console import Group
from storage import models
from analysis import supply_risk, india_trade

def get_risk_panel() -> Panel:
    """Generates the Rich panel covering Supply Constraints, Macro shocks, and Trade Flows."""
    
    # 1. Macro Economic Indicators Table
    macro_table = Table(show_header=True, header_style="bold yellow", expand=True)
    macro_table.add_column("Indicator", style="cyan")
    macro_table.add_column("Value", justify="right")
    macro_table.add_column("Source", style="dim")
    
    query = models.MacroSeries.select().order_by(models.MacroSeries.timestamp.desc())
    latest_macro = {}
    for m in query:
        if m.indicator_name not in latest_macro:
            latest_macro[m.indicator_name] = m
            
    for name, m in latest_macro.items():
        macro_table.add_row(name, f"{m.value:.2f}", m.source)
        
    if not latest_macro:
        macro_table.add_row("US CPI YoY", "Awaiting Data", "-")
        
    # 2. Supply Risk & Geopolitical Dependency Table
    supply_table = Table(show_header=False, expand=True, box=None) # Borderless
    supply_table.add_column("Context")
    supply_table.add_column("Value", justify="right")
    
    # Live evaluate Crude Oil risk
    crude_risk = supply_risk.evaluate_supply_score("Crude Oil")
    c_score = crude_risk["supply_risk_score"]
    c_color = "red" if c_score > 70 else "yellow" if c_score > 40 else "green"
    supply_table.add_row("Crude Oil Base Risk", f"[{c_color}]{c_score}/100[/{c_color}]")
    
    ind_risk = india_trade.evaluate_india_trade_risk("Fuel")
    i_status = ind_risk["status"]
    i_color = "red" if ind_risk["risk_score"] > 10 else "green"
    supply_table.add_row("India Fuel Imports", f"[{i_color}]{i_status}[/{i_color}]")
    
    sanctions_ct = models.SanctionsWatch.select().count()
    s_color = "red" if sanctions_ct > 0 else "green"
    supply_table.add_row("Active Global Sanctions", f"[{s_color}]{sanctions_ct} flagged[/{s_color}]")
    
    group = Group(macro_table, "", supply_table)
    return Panel(group, title="Macro & Supply Risk", border_style="yellow")
