"use client";

import React, { useEffect, useState } from 'react';
import { Search, ChevronDown, CheckCircle2, XCircle } from 'lucide-react';
import axios from 'axios';

interface Transaction {
  id: string;
  date: string;
  raw_string: string;
  amount: number;
  predicted_category: string;
  actual_category: string | null;
  status: string;
}

export default function TransactionTable({ refreshKey, categories }: { refreshKey: number, categories: string[] }) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [search, setSearch] = useState('');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [bulkCategory, setBulkCategory] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await axios.get(`${apiUrl}/api/transactions?search=${search}`);
      setTransactions(response.data.transactions);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, [refreshKey, search]);

  const toggleSelectAll = () => {
    if (selectedIds.length === transactions.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(transactions.map(t => t.id));
    }
  };

  const toggleSelect = (id: string) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter(i => i !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  const handleBulkUpdate = async () => {
    if (!bulkCategory || selectedIds.length === 0) return;

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      await axios.put(`${apiUrl}/api/transactions/bulk`, {
        ids: selectedIds,
        category: bulkCategory
      });
      fetchTransactions();
      setSelectedIds([]);
      setBulkCategory('');
    } catch (error) {
      console.error('Bulk update error:', error);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="p-6 border-b border-gray-100 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h2 className="text-xl font-semibold">Transactions</h2>
        
        <div className="flex flex-wrap items-center gap-3">
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input
              type="text"
              placeholder="Search descriptions..."
              className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-full md:w-64"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          {/* Bulk Actions */}
          {selectedIds.length > 0 && (
            <div className="flex items-center gap-2 bg-blue-50 p-1 rounded-lg border border-blue-100">
              <span className="text-sm font-medium text-blue-700 px-2">{selectedIds.length} selected</span>
              <select
                className="bg-white border border-gray-200 rounded-md text-sm px-2 py-1 outline-none"
                value={bulkCategory}
                onChange={(e) => setBulkCategory(e.target.value)}
              >
                <option value="">Set Category...</option>
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
              <button
                onClick={handleBulkUpdate}
                disabled={!bulkCategory}
                className="bg-blue-600 text-white p-1 rounded hover:bg-blue-700 disabled:opacity-50"
              >
                <CheckCircle2 size={20} />
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              <th className="px-6 py-4">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  checked={selectedIds.length === transactions.length && transactions.length > 0}
                  onChange={toggleSelectAll}
                />
              </th>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600">Date</th>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600">Description</th>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600 text-right">Amount</th>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600">Category</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={5} className="px-6 py-8 text-center text-gray-500">Loading transactions...</td></tr>
            ) : transactions.length === 0 ? (
              <tr><td colSpan={5} className="px-6 py-8 text-center text-gray-500">No transactions found.</td></tr>
            ) : (
              transactions.map((t) => (
                <tr key={t.id} className={`hover:bg-gray-50 transition-colors ${selectedIds.includes(t.id) ? 'bg-blue-50/30' : ''}`}>
                  <td className="px-6 py-4">
                    <input
                      type="checkbox"
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      checked={selectedIds.includes(t.id)}
                      onChange={() => toggleSelect(t.id)}
                    />
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">{t.date}</td>
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{t.raw_string}</td>
                  <td className="px-6 py-4 text-sm font-semibold text-right text-gray-900">
                    ${t.amount.toFixed(2)}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${t.actual_category ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'}`}>
                      {t.actual_category || t.predicted_category}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
