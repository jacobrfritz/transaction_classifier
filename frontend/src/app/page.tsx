"use client";

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Wallet } from 'lucide-react';
import Upload from '@/components/Upload';
import Stats from '@/components/Stats';
import TransactionTable from '@/components/TransactionTable';
import CategoryManager from '@/components/CategoryManager';
import DownloadButton from '@/components/DownloadButton';

export default function Home() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [categories, setCategories] = useState<string[]>([]);

  const fetchCategories = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await axios.get(`${apiUrl}/api/categories`);
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, [refreshKey]);

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <main className="min-h-screen bg-gray-50 pb-12">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-blue-600 p-2 rounded-lg">
              <Wallet className="text-white" size={24} />
            </div>
            <h1 className="text-xl font-bold text-gray-900 tracking-tight">TransacTrack</h1>
          </div>
          <DownloadButton />
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900">Dashboard</h2>
          <p className="text-gray-500 mt-1">Manage and classify your financial transactions with ease.</p>
        </div>

        {/* Stats Row */}
        <Stats refreshKey={refreshKey} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content: Table */}
          <div className="lg:col-span-2 space-y-8">
            <TransactionTable refreshKey={refreshKey} categories={categories} />
          </div>

          {/* Sidebar: Upload & Categories */}
          <div className="space-y-8">
            <Upload onUploadSuccess={handleRefresh} />
            <CategoryManager categories={categories} onUpdate={handleRefresh} />
          </div>
        </div>
      </div>
    </main>
  );
}
