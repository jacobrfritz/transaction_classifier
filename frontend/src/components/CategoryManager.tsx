"use client";

import React, { useState } from 'react';
import { Tag, Plus, Trash2, X } from 'lucide-react';
import axios from 'axios';

export default function CategoryManager({ categories, onUpdate }: { categories: string[], onUpdate: () => void }) {
  const [newCategory, setNewCategory] = useState('');

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCategory.trim()) return;

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      await axios.post(`${apiUrl}/api/categories`, { name: newCategory.trim() });
      setNewCategory('');
      onUpdate();
    } catch (error) {
      console.error('Error adding category:', error);
    }
  };

  const handleDelete = async (name: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      await axios.delete(`${apiUrl}/api/categories/${name}`);
      onUpdate();
    } catch (error) {
      console.error('Error deleting category:', error);
    }
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <Tag size={20} className="text-purple-600" />
        Categories
      </h2>

      <form onSubmit={handleAdd} className="flex gap-2 mb-4">
        <input
          type="text"
          placeholder="New category..."
          className="flex-1 px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
          value={newCategory}
          onChange={(e) => setNewCategory(e.target.value)}
        />
        <button
          type="submit"
          disabled={!newCategory.trim()}
          className="bg-purple-600 text-white p-2 rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
        >
          <Plus size={20} />
        </button>
      </form>

      <div className="flex flex-wrap gap-2">
        {categories.map((cat) => (
          <div
            key={cat}
            className="flex items-center gap-1.5 bg-gray-100 px-3 py-1.5 rounded-full text-sm font-medium text-gray-700 group hover:bg-gray-200 transition-colors"
          >
            {cat}
            <button
              onClick={() => handleDelete(cat)}
              className="text-gray-400 hover:text-red-500 transition-colors"
            >
              <X size={14} />
            </button>
          </div>
        ))}
        {categories.length === 0 && (
          <p className="text-sm text-gray-500 italic">No custom categories yet.</p>
        )}
      </div>
    </div>
  );
}
