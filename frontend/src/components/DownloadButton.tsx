"use client";

import React from 'react';
import { Download as DownloadIcon } from 'lucide-react';

export default function DownloadButton() {
  const handleDownload = () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    window.location.href = `${apiUrl}/api/download`;
  };

  return (
    <button
      onClick={handleDownload}
      className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-green-700 active:scale-[0.98] transition-all"
    >
      <DownloadIcon size={18} />
      Export Classified CSV
    </button>
  );
}
