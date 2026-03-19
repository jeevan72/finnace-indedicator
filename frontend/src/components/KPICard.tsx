'use client';

import { Price } from '@/lib/types';

interface KPICardProps {
  price: Price;
}

function formatINR(value: number): string {
  const intPart = Math.floor(value);
  const decPart = (value - intPart).toFixed(2).slice(1);
  const str = intPart.toString();
  if (str.length <= 3) return str + decPart;
  let result = str.slice(-3);
  let rest = str.slice(0, -3);
  while (rest.length > 0) {
    result = rest.slice(-2) + ',' + result;
    rest = rest.slice(0, -2);
  }
  return result + decPart;
}

export function KPICard({ price }: KPICardProps) {
  const isPositive = price.change_pct > 0;
  const isNegative = price.change_pct < 0;
  const prefix = price.currency === 'INR' ? '₹' : '$';
  const formatted = price.currency === 'INR' 
    ? formatINR(price.price)
    : price.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-gray-900 to-gray-800 p-6 shadow-xl transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl">
      {/* Glow effect */}
      <div className={`absolute -top-8 -right-8 h-24 w-24 rounded-full blur-3xl opacity-30 ${
        isPositive ? 'bg-emerald-500' : isNegative ? 'bg-red-500' : 'bg-gray-500'
      }`} />
      
      <p className="text-sm font-medium text-gray-400 mb-1">{price.name}</p>
      <p className="text-2xl font-bold text-white tracking-tight">
        {prefix}{formatted}
      </p>
      <div className="mt-2 flex items-center gap-2">
        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-sm font-semibold ${
          isPositive 
            ? 'bg-emerald-500/20 text-emerald-400' 
            : isNegative 
            ? 'bg-red-500/20 text-red-400'
            : 'bg-gray-500/20 text-gray-400'
        }`}>
          {isPositive ? '▲' : isNegative ? '▼' : '●'} {Math.abs(price.change_pct).toFixed(2)}%
        </span>
        <span className="text-xs text-gray-500">{price.source}</span>
      </div>
    </div>
  );
}

export function KPIGrid({ prices }: { prices: Price[] }) {
  const topAssets = ['Gold', 'Silver', 'WTI Crude', 'Brent Crude'];
  const kpiPrices = topAssets
    .map(name => prices.find(p => p.symbol.includes(name) || p.name.includes(name)))
    .filter(Boolean) as Price[];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {kpiPrices.map(p => (
        <KPICard key={p.symbol} price={p} />
      ))}
    </div>
  );
}
