"use client";

import React, { useState } from 'react';
import { Upload as UploadIcon, FileCheck, AlertCircle, Columns } from 'lucide-react';
import axios from 'axios';

export default function Upload({ onUploadSuccess }: { onUploadSuccess: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  
  // Mapping state
  const [mappingRequired, setMappingRequired] = useState(false);
  const [csvHeaders, setCsvHeaders] = useState<string[]>([]);
  const [dateCol, setDateCol] = useState('');
  const [amountCol, setAmountCol] = useState('');
  const [descriptionCol, setDescriptionCol] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
      setMessage(null);
      setMappingRequired(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setMessage(null);
      setMappingRequired(false);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setMessage(null);

    const formData = new FormData();
    formData.append('file', file);
    
    if (mappingRequired) {
      if (!dateCol || !amountCol || !descriptionCol) {
        setMessage({ type: 'error', text: 'Please map all required columns.' });
        setUploading(false);
        return;
      }
      formData.append('date_col', dateCol);
      formData.append('amount_col', amountCol);
      formData.append('description_col', descriptionCol);
    }

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await axios.post(`${apiUrl}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      const { status, message, headers } = response.data;
      
      if (status === 'mapping_required') {
        setMappingRequired(true);
        setCsvHeaders(headers || []);
        setMessage({ type: 'error', text: 'Column mapping required for this CSV format.' });
      } else {
        setMessage({ 
          type: status === 'success' ? 'success' : 'error', 
          text: message 
        });

        if (status === 'success') {
          setFile(null);
          setMappingRequired(false);
          onUploadSuccess();
        }
      }
    } catch (error) {
      console.error('Upload error:', error);
      setMessage({ type: 'error', text: 'Failed to upload file.' });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <UploadIcon size={20} className="text-blue-600" />
        Upload Transactions
      </h2>
      <div className="flex flex-col gap-4">
        {!mappingRequired ? (
          <div className="flex items-center justify-center w-full">
            <label 
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors"
            >
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                <UploadIcon className="w-8 h-8 mb-3 text-gray-400" />
                <p className="mb-2 text-sm text-gray-500">
                  <span className="font-semibold">Click to upload</span> or drag and drop
                </p>
                <p className="text-xs text-gray-400">CSV files only</p>
              </div>
              <input type="file" className="hidden" accept=".csv" onChange={handleFileChange} />
            </label>
          </div>
        ) : (
          <div className="bg-orange-50 p-4 rounded-lg border border-orange-100">
            <h3 className="text-sm font-medium text-orange-800 mb-3 flex items-center gap-2">
              <Columns size={16} />
              Map CSV Columns
            </h3>
            <div className="grid gap-3">
              <div>
                <label className="block text-xs text-orange-700 mb-1">Date Column</label>
                <select 
                  value={dateCol} 
                  onChange={(e) => setDateCol(e.target.value)}
                  className="w-full p-2 text-sm rounded border border-orange-200 bg-white text-gray-900"
                >
                  <option value="" className="text-gray-500">Select column...</option>
                  {csvHeaders.map(h => <option key={h} value={h} className="text-gray-900">{h}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs text-orange-700 mb-1">Amount Column</label>
                <select 
                  value={amountCol} 
                  onChange={(e) => setAmountCol(e.target.value)}
                  className="w-full p-2 text-sm rounded border border-orange-200 bg-white text-gray-900"
                >
                  <option value="" className="text-gray-500">Select column...</option>
                  {csvHeaders.map(h => <option key={h} value={h} className="text-gray-900">{h}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs text-orange-700 mb-1">Description Column</label>
                <select 
                  value={descriptionCol} 
                  onChange={(e) => setDescriptionCol(e.target.value)}
                  className="w-full p-2 text-sm rounded border border-orange-200 bg-white text-gray-900"
                >
                  <option value="" className="text-gray-500">Select column...</option>
                  {csvHeaders.map(h => <option key={h} value={h} className="text-gray-900">{h}</option>)}
                </select>
              </div>
              <button 
                onClick={() => setMappingRequired(false)}
                className="text-xs text-orange-600 hover:underline text-left mt-1"
              >
                Cancel and pick another file
              </button>
            </div>
          </div>
        )}
        
        {file && !mappingRequired && (
          <div className="flex items-center gap-2 text-sm text-gray-600 bg-blue-50 p-2 rounded">
            <FileCheck size={16} className="text-blue-500" />
            {file.name}
          </div>
        )}

        {message && (
          <div className={`flex items-center gap-2 text-sm p-2 rounded ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
            {message.type === 'success' ? <FileCheck size={16} /> : <AlertCircle size={16} />}
            {message.text}
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className={`w-full py-2 px-4 rounded-lg font-medium transition-all ${
            !file || uploading
              ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700 active:scale-[0.98]'
          }`}
        >
          {uploading ? 'Processing...' : mappingRequired ? 'Save Mapping & Process' : 'Process CSV'}
        </button>
      </div>
    </div>
  );
}
