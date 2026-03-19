'use client';

import { Price } from '@/lib/types';

interface PriceTableProps {
  title: string;
  emoji: string;
  prices: Price[];
  assetNames: string[];
}

export function PriceTable({ title, emoji, prices, assetNames }: PriceTableProps) {
  const filtered = prices.filter(p => assetNames.some(a => p.name.includes(a)));
  
  if (filtered.length === 0) return null;

  return (
    <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-gray-900 to-gray-800 p-5 shadow-xl">
      <h3 className="text-base font-semibold text-white mb-3">
        {emoji} {title}
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left py-2 text-gray-400 font-medium">Asset</th>
              <th className="text-right py-2 text-gray-400 font-medium">Price</th>
              <th className="text-right py-2 text-gray-400 font-medium">Change</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(p => {
              const prefix = p.currency === 'INR' ? '₹' : '$';
              const isPos = p.change_pct > 0;
              const isNeg = p.change_pct < 0;
              return (
                <tr key={p.symbol} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                  <td className="py-2.5 text-gray-200">
                    {p.is_delayed && <span className="text-yellow-500 text-xs mr-1">[D]</span>}
                    {p.name}
                  </td>
                  <td className="py-2.5 text-right text-white font-mono">
                    {prefix}{p.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </td>
                  <td className={`py-2.5 text-right font-semibold ${
                    isPos ? 'text-emerald-400' : isNeg ? 'text-red-400' : 'text-gray-400'
                  }`}>
                    {isPos ? '▲' : isNeg ? '▼' : '●'} {Math.abs(p.change_pct).toFixed(2)}%
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
