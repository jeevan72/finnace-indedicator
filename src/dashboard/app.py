import sys
from pathlib import Path

# Provide resolving access to core src
SRC_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(SRC_DIR))

import streamlit as st
import pandas as pd
import plotly.express as px
from storage import models
from storage.db import init_db

st.set_page_config(page_title="Financial Intelligence Dashboard", layout="wide", page_icon="📈")

# Initialize database to ensure access
init_db()

st.title("Personal Financial Intelligence Terminal")
st.markdown("Phase 2 User Interface - Aggregating local intelligence from SQL backend.")

tab_prices, tab_options, tab_supply = st.tabs(["Global Prices", "NSE Options", "Supply & Macro"])

with tab_prices:
    st.subheader("Live Commodity & Index Prices")
    
    # Query peewee into pandas DataFrame
    # Distinct on symbol since we want the latest
    records = models.Prices.select().order_by(models.Prices.timestamp.desc())
    latest_px = {}
    for r in records:
        if r.symbol not in latest_px:
            latest_px[r.symbol] = r
            
    if latest_px:
        df = pd.DataFrame([r.__data__ for r in latest_px.values()])
        df = df[["name", "symbol", "price", "change_pct", "volume", "source", "timestamp"]]
        
        # Color formatting map
        def color_change(val):
            color = 'lightgreen' if val > 0 else 'salmon' if val < 0 else 'white'
            return f'color: {color}'
        
        # --- Top 10 Metals & Commodities Chart ---
        from config.assets import METALS, ENERGY, INDICES, FOREX
        tracked_commodities = set(METALS + ENERGY)
        
        # 1. KPI Columns for Top 4 Commodities
        top_kpis = ["Gold", "Silver", "WTI Crude", "Brent Crude"]
        cols = st.columns(4)
        for i, sym in enumerate(top_kpis):
            filtered = [r for r in latest_px.values() if sym in r.symbol] # Matches Gold (10g)
            if filtered:
                r = filtered[0]
                with cols[i]:
                    # Format as Indian numbering for INR, standard for USD
                    prefix = "₹" if getattr(r, 'currency', 'USD') == 'INR' else "$"
                    price_str = f"{prefix} {r.price:,.2f}" if prefix == "$" else f"{prefix} {r.price:,.2f}" # Python format handles , well
                    st.metric(label=r.name, value=price_str, delta=f"{r.change_pct:+.2f}%")

        st.divider()

        # 2. Daily Change Bar Chart
        chart_list = [r.__data__ for r in latest_px.values() if any(c in r.name for c in tracked_commodities)]
        if chart_list:
            df_chart = pd.DataFrame(chart_list)
            df_chart = df_chart.sort_values(by="change_pct", ascending=True)
            fig = px.bar(
                df_chart, 
                x="change_pct", 
                y="name", 
                orientation="h",
                color="change_pct", 
                color_continuous_scale=["salmon", "lightgrey", "lightgreen"],
                color_continuous_midpoint=0,
                title="Top Metals & Commodities — Day Change %"
            )
            fig.update_layout(showlegend=False, xaxis_title="Change %", yaxis_title="")
            st.plotly_chart(fig)
            
        # 3. Categorized Data Tables
        st.markdown("### Market Details")
        
        def display_category(title, asset_list):
            cat_list = [r.__data__ for r in latest_px.values() if any(a in r.name for a in asset_list)]
            if cat_list:
                df_cat = pd.DataFrame(cat_list)
                df_cat = df_cat[["name", "price", "change_pct", "currency", "timestamp", "source"]]
                st.markdown(f"**{title}**")
                st.dataframe(df_cat.style.map(color_change, subset=['change_pct']))

        col1, col2 = st.columns(2)
        with col1:
            display_category("🥇 Precious & Base Metals", METALS)
            display_category("🛢️ Energy", ENERGY)
        with col2:
            display_category("📈 Global Indices", INDICES)
            display_category("💱 Forex & Volatility", FOREX + ["VIX", "OVX", "GVZ"])
            
    else:
        st.info("No pricing data found in DB. Run the CLI fetcher daemon.")

with tab_options:
    st.subheader("NSE Options Snapshots")
    opts = models.OptionsSnapshot.select().order_by(models.OptionsSnapshot.timestamp.desc())
    latest_opts = {}
    for o in opts:
        if o.symbol not in latest_opts:
            latest_opts[o.symbol] = o
            
    if latest_opts:
        df_opts = pd.DataFrame([o.__data__ for o in latest_opts.values()])
        st.dataframe(df_opts)
    else:
        st.info("No options data found in DB.")

with tab_supply:
    st.subheader("Recent Corporate & Supply Events")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**BSE Announcements**")
        events = models.Events.select().order_by(models.Events.timestamp.desc()).limit(15)
        if events:
            for e in events:
                st.caption(f"**{e.symbol}** [{e.event_type}] - {e.headline} ({e.timestamp})")
        else:
            st.info("No alerts.")
            
    with col2:
        st.markdown("**Geopolitical Risk & Sanctions**")
        sanctions = models.SanctionsWatch.select().order_by(models.SanctionsWatch.id.desc()).limit(15)
        if sanctions:
            df_sanc = pd.DataFrame([s.__data__ for s in sanctions])
            st.dataframe(df_sanc[["entity_name", "asset_type", "added_date"]])
        else:
            st.info("No active sanctions tracked.")
