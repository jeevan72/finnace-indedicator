'use client';

import { useEffect, useState } from 'react';
import { Price } from '@/lib/types';
import { getPrices, connectPricesWebSocket, triggerFetchAll } from '@/lib/api';
import { KPIGrid } from '@/components/KPICard';
import { DayChangeChart } from '@/components/PriceChart';
import { PriceTable } from '@/components/PriceTable';

const METALS = ['Gold', 'Silver', 'Copper', 'Nickel', 'Lithium', 'Cobalt'];
const ENERGY = ['WTI Crude', 'Brent Crude', 'Natural Gas', 'Coal'];
const INDICES = ['Nifty', 'Sensex', 'S&P 500', 'NASDAQ', 'DAX', 'FTSE', 'Nikkei'];
const FOREX_VOL = ['USD/INR', 'DXY', 'EUR/USD', 'CNY/USD', 'VIX', 'OVX', 'GVZ'];

export default function Dashboard() {
  const [prices, setPrices] = useState<Price[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [fetching, setFetching] = useState(false);

  // Initial REST fetch
  useEffect(() => {
    getPrices()
      .then(data => {
        setPrices(data);
        setLastUpdate(new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata' }));
      })
      .catch(err => console.error('Failed to load prices:', err))
      .finally(() => setLoading(false));
  }, []);

  // WebSocket for live updates
  useEffect(() => {
    const ws = connectPricesWebSocket((data) => {
      if (data && data.length > 0) {
        setPrices(data);
        setLastUpdate(new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata' }));
      }
    });
    return () => { ws?.close(); };
  }, []);

  const handleRefresh = async () => {
    setFetching(true);
    try {
      await triggerFetchAll();
      // Wait a moment for DB to update, then re-fetch
      await new Promise(r => setTimeout(r, 2000));
      const data = await getPrices();
      setPrices(data);
      setLastUpdate(new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata' }));
    } catch (err) {
      console.error('Fetch all failed:', err);
    } finally {
      setFetching(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 rounded-full border-4 border-emerald-500 border-t-transparent animate-spin" />
          <p className="text-gray-400">Loading market data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header row with refresh */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Market Overview</h2>
          <p className="text-sm text-gray-500">
            {lastUpdate ? `Last updated: ${lastUpdate} IST` : 'Waiting for data...'}
            {prices.length > 0 && ` • ${prices.length} assets tracked`}
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={fetching}
          className="rounded-xl bg-gradient-to-r from-emerald-600 to-cyan-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-500/25 transition-all hover:shadow-emerald-500/40 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {fetching ? '⟳ Fetching...' : '⟳ Refresh All'}
        </button>
      </div>

      {/* KPI Cards */}
      <KPIGrid prices={prices} />

      {/* Day Change Chart */}
      <DayChangeChart prices={prices} />

      {/* Categorized Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <PriceTable title="Precious & Base Metals" emoji="🥇" prices={prices} assetNames={METALS} />
        <PriceTable title="Energy" emoji="🛢️" prices={prices} assetNames={ENERGY} />
        <PriceTable title="Global Indices" emoji="📈" prices={prices} assetNames={INDICES} />
        <PriceTable title="Forex & Volatility" emoji="💱" prices={prices} assetNames={FOREX_VOL} />
      </div>

      {/* Footer */}
      <div className="text-center text-xs text-gray-600 pt-8 pb-4">
        Financial Intelligence Terminal v2.0 • Data from Yahoo Finance, NSE, BSE, FRED
      </div>
    </div>
  );
}
