'use client';

import { Price } from '@/lib/types';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, Cell,
} from 'recharts';

interface PriceChartProps {
  prices: Price[];
}

export function DayChangeChart({ prices }: PriceChartProps) {
  const commodities = ['Gold', 'Silver', 'Copper', 'Nickel', 'WTI Crude', 'Brent Crude', 'Natural Gas', 'Coal'];
  
  const data = prices
    .filter(p => commodities.some(c => p.name.includes(c)))
    .map(p => ({
      name: p.name.length > 15 ? p.name.slice(0, 12) + '...' : p.name,
      change: parseFloat(p.change_pct.toFixed(2)),
    }))
    .sort((a, b) => a.change - b.change);

  if (data.length === 0) return null;

  return (
    <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-gray-900 to-gray-800 p-6 shadow-xl">
      <h3 className="text-lg font-semibold text-white mb-4">
        Metals & Commodities — Day Change %
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} layout="vertical" margin={{ left: 80, right: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis type="number" tick={{ fill: '#9CA3AF', fontSize: 12 }} />
          <YAxis 
            type="category" 
            dataKey="name" 
            tick={{ fill: '#D1D5DB', fontSize: 13 }} 
            width={80}
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px' }}
            labelStyle={{ color: '#F9FAFB' }}
            formatter={(value: any) => [`${value}%`, 'Change']}
          />
          <Bar dataKey="change" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell 
                key={index} 
                fill={entry.change >= 0 ? '#10B981' : '#EF4444'} 
                fillOpacity={0.85}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
