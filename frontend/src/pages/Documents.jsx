import React, { useState, useEffect, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  Trash2,
  ListTree,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  FolderOpen,
  X,
  FileCheck,
  Tag
} from 'lucide-react';
import { api } from '../services/api';

export default function Documents() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState('');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [selectedHierarchy, setSelectedHierarchy] = useState(null);
  const fileInputRef = useRef(null);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const data = await api.getDocuments();
      setDocuments(data);
      setError(null);
    } catch (err) {
      console.error('Failed to load documents:', err);
      setError('Could not fetch documents. Verify that the backend is active.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileUpload = async (file) => {
    if (!file) return;

    const allowed = ['.pdf', '.docx', '.txt'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowed.includes(ext)) {
      setError(`Unsupported format. Only ${allowed.join(', ')} are supported.`);
      return;
    }

    if (file.size > 25 * 1024 * 1024) {
      setError('File exceeds maximum size limit of 25 MB.');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);
    setUploadProgress('Extracting text and identifying syllabus structure...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      setUploadProgress('Generating semantic chunks and vector embeddings in ChromaDB...');
      const uploadedDoc = await api.uploadDocument(formData);
      setSuccess(`Successfully ingested '${uploadedDoc.filename}' (${uploadedDoc.chunk_count} chunks indexed).`);
      await fetchDocuments();
    } catch (err) {
      console.error('Upload failed:', err);
      setError(`Upload failed: ${err.message || 'Unknown processing error'}`);
    } finally {
      setUploading(false);
      setUploadProgress('');
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (id, filename) => {
    if (!window.confirm(`Are you sure you want to delete '${filename}'? All associated vector embeddings will be removed.`)) {
      return;
    }

    try {
      await api.deleteDocument(id);
      setSuccess(`Deleted '${filename}' from vector database.`);
      fetchDocuments();
    } catch (err) {
      setError(`Failed to delete document: ${err.message}`);
    }
  };

  const handleViewHierarchy = async (docId) => {
    try {
      const res = await api.getDocumentHierarchy(docId);
      setSelectedHierarchy(res);
    } catch (err) {
      setError('Could not fetch syllabus hierarchy for this document.');
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-black text-slate-900 tracking-tight">
          Document Ingestion & Syllabus Outline
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Upload PDF, DOCX, or TXT curriculum materials. The Document Agent extracts text, builds a concept hierarchy,
          and indexes semantic chunks into ChromaDB for context-grounded retrieval.
        </p>
      </div>

      {/* Alert Notices */}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 shrink-0 text-red-600" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="p-1 hover:bg-red-100 rounded">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {success && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 shrink-0 text-emerald-600" />
            <span>{success}</span>
          </div>
          <button onClick={() => setSuccess(null)} className="p-1 hover:bg-emerald-100 rounded">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Drag & Drop Upload Zone */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileUpload(e.dataTransfer.files[0]);
          }
        }}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center transition-all duration-200 cursor-pointer ${
          uploading
            ? 'border-violet-400 bg-violet-50/50 cursor-not-allowed'
            : 'border-slate-300 hover:border-violet-500 hover:bg-violet-50/20 bg-white shadow-xs'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileUpload(e.target.files[0]);
            }
          }}
          disabled={uploading}
        />

        <div className="flex flex-col items-center max-w-md mx-auto">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-violet-600 to-indigo-600 text-white flex items-center justify-center shadow-md shadow-violet-500/20 mb-4">
            {uploading ? (
              <RefreshCw className="w-8 h-8 animate-spin" />
            ) : (
              <UploadCloud className="w-8 h-8" />
            )}
          </div>

          <h3 className="text-lg font-bold text-slate-800 mb-1">
            {uploading ? 'Processing Educational Document...' : 'Upload Academic Course Material'}
          </h3>
          <p className="text-xs sm:text-sm text-slate-500 mb-4">
            {uploading
              ? uploadProgress
              : 'Drag & drop your files here, or browse your device (Max 25 MB)'}
          </p>

          {!uploading && (
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200">
              <span>Supported Formats:</span>
              <span className="text-violet-600 font-mono font-bold">.PDF</span>
              <span>•</span>
              <span className="text-violet-600 font-mono font-bold">.DOCX</span>
              <span>•</span>
              <span className="text-violet-600 font-mono font-bold">.TXT</span>
            </div>
          )}
        </div>
      </div>

      {/* Document Library Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="font-bold text-base text-slate-900">Indexed Course Library</h3>
            <p className="text-xs text-slate-400">Materials active in the RAG vector store</p>
          </div>
          <button
            onClick={fetchDocuments}
            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition"
            title="Refresh Library"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {documents.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <FolderOpen className="w-12 h-12 stroke-1 mx-auto mb-3" />
            <p className="text-sm font-medium">No documents uploaded yet.</p>
            <p className="text-xs mt-1">Upload a syllabus or lecture notes to get started.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50/80 text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3.5">Document Name</th>
                  <th className="px-6 py-3.5">Subject</th>
                  <th className="px-6 py-3.5">Chunks</th>
                  <th className="px-6 py-3.5">Extracted Topics</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/60 transition">
                    <td className="px-6 py-4 font-semibold text-slate-900 flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center shrink-0">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div>
                        <p className="truncate max-w-xs">{doc.filename}</p>
                        <p className="text-[11px] text-slate-400">
                          {(doc.file_size_bytes / 1024).toFixed(1)} KB • {doc.file_type.toUpperCase()}
                        </p>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-xs font-medium text-slate-700">
                      {doc.subject}
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 text-xs font-semibold">
                        {doc.chunk_count} chunks
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1 max-w-sm">
                        {doc.topics.slice(0, 3).map((t, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 rounded text-[11px] bg-violet-50 text-violet-700 font-medium"
                          >
                            {t}
                          </span>
                        ))}
                        {doc.topics.length > 3 && (
                          <span className="text-[10px] text-slate-400 self-center">
                            +{doc.topics.length - 3} more
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleViewHierarchy(doc.id)}
                          className="px-2.5 py-1.5 rounded-lg text-xs font-semibold text-violet-700 hover:bg-violet-50 transition flex items-center gap-1 border border-violet-200"
                          title="View Syllabus Outline"
                        >
                          <ListTree className="w-3.5 h-3.5" />
                          <span>Outline</span>
                        </button>
                        <button
                          onClick={() => handleDelete(doc.id, doc.filename)}
                          className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
                          title="Delete Document"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Syllabus & Topic Hierarchy Modal */}
      {selectedHierarchy && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <ListTree className="w-5 h-5 text-violet-600" />
                <h3 className="font-bold text-base text-slate-900">
                  Detected Syllabus Hierarchy
                </h3>
              </div>
              <button
                onClick={() => setSelectedHierarchy(null)}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <p className="text-xs text-slate-400">File: <span className="font-semibold text-slate-700">{selectedHierarchy.filename}</span></p>
              <p className="text-xs text-slate-400 mt-0.5">Subject: <span className="font-semibold text-slate-700">{selectedHierarchy.subject}</span></p>
            </div>

            <div className="max-h-72 overflow-y-auto space-y-2 pr-1">
              {selectedHierarchy.topics.map((item, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-slate-50 border border-slate-200/60">
                  <div className="flex items-center gap-2 font-semibold text-xs text-slate-800">
                    <Tag className="w-3.5 h-3.5 text-violet-600" />
                    <span>{item.name}</span>
                  </div>
                  {item.subtopics && item.subtopics.length > 0 && (
                    <ul className="mt-2 pl-6 list-disc space-y-1 text-[11px] text-slate-500">
                      {item.subtopics.map((sub, sIdx) => (
                        <li key={sIdx}>{sub}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>

            <div className="pt-2 text-right">
              <button
                onClick={() => setSelectedHierarchy(null)}
                className="px-4 py-2 rounded-xl bg-violet-600 text-white font-semibold text-xs hover:bg-violet-700 transition"
              >
                Close Outline
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
