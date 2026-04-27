"use client";

import React, { useEffect, useState } from 'react';
import { BarChart3, PieChart, TrendingUp, DollarSign } from 'lucide-react';
import axios from 'axios';

interface CategoryStat {
  category: string;
  count: number;
  percentage: number;
}

interface StatsData {
  total: number;
  breakdown: CategoryStat[];
}

export default function Stats({ refreshKey }: { refreshKey: number }) {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await axios.get(`${apiUrl}/api/stats`);
        setStats(response.data);
      } catch (error) {
        console.error('Error fetching stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [refreshKey]);

  if (loading) return <div className="h-48 flex items-center justify-center">Loading stats...</div>;
  if (!stats) return null;

  const topCategory = stats.breakdown.sort((a, b) => b.count - a.count)[0];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
      <StatCard
        title="Total Transactions"
        value={stats.total.toString()}
        icon={<BarChart3 className="text-blue-600" size={24} />}
        color="bg-blue-50"
      />
      <StatCard
        title="Top Category"
        value={topCategory ? `${topCategory.category} (${topCategory.count})` : 'N/A'}
        icon={<TrendingUp className="text-purple-600" size={24} />}
        color="bg-purple-50"
      />
      <StatCard
        title="Categories"
        value={stats.breakdown.length.toString()}
        icon={<PieChart className="text-orange-600" size={24} />}
        color="bg-orange-50"
      />
    </div>
  );
}

function StatCard({ title, value, icon, color }: { title: string; value: string; icon: React.ReactNode; color: string }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
      <div className={`p-3 rounded-lg ${color}`}>
        {icon}
      </div>
      <div>
        <p className="text-sm text-gray-500 font-medium">{title}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
      </div>
    </div>
  );
}
