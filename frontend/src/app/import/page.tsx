'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useCenterContext } from '@/hooks/useCenterContext';
import { useAuth } from '@/contexts/AuthContext';

// ── Types ──────────────────────────────────────────────────────────────────────

type ImportType = 'leads' | 'enrollments' | 'attendance' | 'skills';

interface ImportTypeOption {
  key: ImportType;
  label: string;
  description: string;
  icon: React.ReactNode;
}

interface FieldMapping {
  targetField: string;
  label: string;
  required: boolean;
  csvColumn: string; // '' means unmapped
}

interface ImportResult {
  created: number;
  updated: number;
  skipped: number;
  errors: { row: number; field: string; message: string }[];
}

// ── Field Definitions per import type ──────────────────────────────────────────

const IMPORT_FIELDS: Record<ImportType, { targetField: string; label: string; required: boolean }[]> = {
  leads: [
    { targetField: 'child_first_name', label: 'Child First Name', required: true },
    { targetField: 'child_last_name', label: 'Child Last Name', required: false },
    { targetField: 'child_dob', label: 'Child DOB', required: false },
    { targetField: 'child_age', label: 'Child Age', required: false },
    { targetField: 'child_school', label: 'School', required: false },
    { targetField: 'child_interests', label: 'Interests', required: false },
    { targetField: 'parent_name', label: 'Parent Name', required: true },
    { targetField: 'parent_phone', label: 'Parent Phone', required: true },
    { targetField: 'parent_email', label: 'Parent Email', required: false },
    { targetField: 'source', label: 'Lead Source', required: false },
    { targetField: 'status', label: 'Lead Status', required: false },
    { targetField: 'discovery_notes', label: 'Discovery Notes', required: false },
    { targetField: 'enquiry_id', label: 'Enquiry ID', required: false },
  ],
  enrollments: [
    { targetField: 'child_first_name', label: 'Child First Name', required: true },
    { targetField: 'child_last_name', label: 'Child Last Name', required: false },
    { targetField: 'parent_phone', label: 'Parent Phone', required: true },
    { targetField: 'plan_type', label: 'Plan Type', required: true },
    { targetField: 'start_date', label: 'Start Date', required: true },
    { targetField: 'end_date', label: 'End Date', required: false },
    { targetField: 'visits_included', label: 'Visits Included', required: false },
    { targetField: 'days_selected', label: 'Days Selected', required: false },
    { targetField: 'batch_name', label: 'Batch Name', required: false },
    { targetField: 'payment_amount', label: 'Payment Amount', required: false },
    { targetField: 'payment_method', label: 'Payment Method', required: false },
    { targetField: 'discount_type', label: 'Discount Type', required: false },
    { targetField: 'discount_value', label: 'Discount Value', required: false },
    { targetField: 'discount_reason', label: 'Discount Reason', required: false },
    { targetField: 'status', label: 'Enrollment Status', required: false },
  ],
  attendance: [
    { targetField: 'child_first_name', label: 'Child First Name', required: true },
    { targetField: 'child_last_name', label: 'Child Last Name', required: false },
    { targetField: 'parent_phone', label: 'Parent Phone', required: false },
    { targetField: 'enquiry_id', label: 'Enquiry ID', required: false },
    { targetField: 'session_date', label: 'Session Date', required: true },
    { targetField: 'batch_name', label: 'Batch Name', required: true },
    { targetField: 'status', label: 'Attendance Status', required: true },
    { targetField: 'notes', label: 'Notes', required: false },
  ],
  skills: [
    { targetField: 'child_first_name', label: 'Child First Name', required: true },
    { targetField: 'child_last_name', label: 'Child Last Name', required: false },
    { targetField: 'parent_phone', label: 'Parent Phone', required: false },
    { targetField: 'enquiry_id', label: 'Enquiry ID', required: false },
    { targetField: 'curriculum_name', label: 'Curriculum Name', required: true },
    { targetField: 'skill_name', label: 'Skill Name', required: true },
    { targetField: 'level', label: 'Skill Level', required: true },
    { targetField: 'notes', label: 'Notes', required: false },
  ],
};

// ── Import Type Cards ──────────────────────────────────────────────────────────

const IMPORT_TYPE_OPTIONS: ImportTypeOption[] = [
  {
    key: 'leads',
    label: 'Leads',
    description: 'Import child + parent + lead status data from your discovery/enquiry sheets.',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
      </svg>
    ),
  },
  {
    key: 'enrollments',
    label: 'Enrollments',
    description: 'Import active students with enrollment plans, payments, and batch assignments.',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    key: 'attendance',
    label: 'Attendance',
    description: 'Import historical attendance records for class sessions.',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
      </svg>
    ),
  },
  {
    key: 'skills',
    label: 'Skills Progress',
    description: 'Import curriculum skill progress levels for students.',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
      </svg>
    ),
  },
];

// ── Helper: Parse CSV header row in the browser ────────────────────────────────

function parseCsvHeaders(text: string): string[] {
  const firstLine = text.split(/\r?\n/)[0] || '';
  // Simple CSV parse: split on comma, trim quotes
  return firstLine.split(',').map((h) => h.trim().replace(/^"|"$/g, '').trim());
}

function parseCsvRows(text: string, maxRows: number): string[][] {
  const lines = text.split(/\r?\n/).filter((l) => l.trim() !== '');
  const rows: string[][] = [];
  // skip header (index 0), take next maxRows
  for (let i = 1; i <= Math.min(maxRows, lines.length - 1); i++) {
    rows.push(lines[i].split(',').map((c) => c.trim().replace(/^"|"$/g, '').trim()));
  }
  return rows;
}

// ── Normalize helper for auto-mapping ──────────────────────────────────────────

function normalize(s: string): string {
  return s.toLowerCase().replace(/[\s_\-]+/g, '');
}

// ── Component ──────────────────────────────────────────────────────────────────

export default function CsvImportPage() {
  const { selectedCenter } = useCenterContext();
  const { user } = useAuth();

  // Wizard state
  const [step, setStep] = useState(1);
  const [importType, setImportType] = useState<ImportType | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [csvHeaders, setCsvHeaders] = useState<string[]>([]);
  const [csvPreviewRows, setCsvPreviewRows] = useState<string[][]>([]);
  const [fieldMappings, setFieldMappings] = useState<FieldMapping[]>([]);

  // Import execution
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Drag & drop
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

  // ── Role guard ──────────────────────────────────────────────────────────────

  const isAllowed = user?.role === 'SUPER_ADMIN' || user?.role === 'CENTER_ADMIN';

  // ── Step 1: Select import type ──────────────────────────────────────────────

  const handleSelectType = (type: ImportType) => {
    setImportType(type);
    setFile(null);
    setCsvHeaders([]);
    setCsvPreviewRows([]);
    setFieldMappings([]);
    setImportResult(null);
    setError(null);
    setStep(2);
  };

  // ── Step 2: File upload ─────────────────────────────────────────────────────

  const processFile = useCallback(
    (f: File) => {
      if (!f.name.toLowerCase().endsWith('.csv')) {
        setError('Please upload a .csv file.');
        return;
      }
      if (f.size > 10 * 1024 * 1024) {
        setError('File size must be under 10 MB.');
        return;
      }
      setError(null);
      setFile(f);

      // Read the file to extract headers + preview rows
      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target?.result as string;
        const headers = parseCsvHeaders(text);
        const previewRows = parseCsvRows(text, 5);
        setCsvHeaders(headers);
        setCsvPreviewRows(previewRows);

        // Auto-build field mappings for the selected import type
        if (importType) {
          const fields = IMPORT_FIELDS[importType];
          const mappings: FieldMapping[] = fields.map((field) => {
            // Try auto-map: if any CSV header normalizes to match the target field name
            const autoMatch = headers.find(
              (h) => normalize(h) === normalize(field.targetField) || normalize(h) === normalize(field.label)
            );
            return {
              targetField: field.targetField,
              label: field.label,
              required: field.required,
              csvColumn: autoMatch || '',
            };
          });
          setFieldMappings(mappings);
        }
      };
      reader.onerror = () => {
        setError('Failed to read file. Please try again.');
      };
      reader.readAsText(f);
    },
    [importType]
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) processFile(f);
  };

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const f = e.dataTransfer.files?.[0];
      if (f) processFile(f);
    },
    [processFile]
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const proceedToMapping = () => {
    if (!file) return;
    setStep(3);
  };

  // ── Step 3: Column mapping ──────────────────────────────────────────────────

  const handleMappingChange = (targetField: string, csvColumn: string) => {
    setFieldMappings((prev) =>
      prev.map((m) => (m.targetField === targetField ? { ...m, csvColumn } : m))
    );
  };

  const allRequiredMapped = fieldMappings
    .filter((m) => m.required)
    .every((m) => m.csvColumn !== '');

  const proceedToPreview = () => {
    if (!allRequiredMapped) {
      setError('Please map all required fields before continuing.');
      return;
    }
    setError(null);
    setStep(4);
  };

  // ── Step 4: Preview ─────────────────────────────────────────────────────────

  const getMappedPreviewData = (): { headers: string[]; rows: string[][] } => {
    const activeMappings = fieldMappings.filter((m) => m.csvColumn !== '');
    const headers = activeMappings.map((m) => m.label);
    const rows = csvPreviewRows.map((row) =>
      activeMappings.map((m) => {
        const colIndex = csvHeaders.indexOf(m.csvColumn);
        return colIndex >= 0 ? row[colIndex] || '' : '';
      })
    );
    return { headers, rows };
  };

  // ── Step 5: Execute import ──────────────────────────────────────────────────

  const executeImport = async () => {
    if (!file || !importType || !selectedCenter) return;

    setImporting(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');

      // Build the column mapping JSON
      const mappingObj: Record<string, string> = {};
      fieldMappings
        .filter((m) => m.csvColumn !== '')
        .forEach((m) => {
          mappingObj[m.targetField] = m.csvColumn;
        });

      const formData = new FormData();
      formData.append('file', file);
      formData.append('column_mapping', JSON.stringify(mappingObj));
      formData.append('center_id', String(selectedCenter.id));

      const response = await fetch(`${API_BASE_URL}/api/v1/import/${importType}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => null);
        throw new Error(errData?.detail || `Import failed with status ${response.status}`);
      }

      const result: ImportResult = await response.json();
      setImportResult(result);
      setStep(5);
    } catch (err: any) {
      setError(err.message || 'Import failed. Please try again.');
    } finally {
      setImporting(false);
    }
  };

  // ── Reset wizard ────────────────────────────────────────────────────────────

  const resetWizard = () => {
    setStep(1);
    setImportType(null);
    setFile(null);
    setCsvHeaders([]);
    setCsvPreviewRows([]);
    setFieldMappings([]);
    setImportResult(null);
    setError(null);
  };

  // ── Render guards ───────────────────────────────────────────────────────────

  if (!isAllowed) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <svg className="w-12 h-12 text-red-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="text-lg font-semibold text-red-800">Access Denied</h3>
          <p className="text-red-600 mt-1">Only Super Admins and Center Admins can access the CSV import tool.</p>
        </div>
      </div>
    );
  }

  if (!selectedCenter) {
    return (
      <div className="p-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <svg className="w-12 h-12 text-yellow-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="text-lg font-semibold text-yellow-800">No Center Selected</h3>
          <p className="text-yellow-600 mt-1">Please select a center from the top bar before importing data.</p>
        </div>
      </div>
    );
  }

  // ── Step progress indicator ─────────────────────────────────────────────────

  const stepLabels = ['Select Type', 'Upload CSV', 'Map Columns', 'Preview', 'Results'];

  const renderStepIndicator = () => (
    <div className="flex items-center justify-center mb-8">
      {stepLabels.map((label, idx) => {
        const stepNum = idx + 1;
        const isActive = step === stepNum;
        const isCompleted = step > stepNum;
        return (
          <div key={label} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${
                  isActive
                    ? 'bg-indigo-600 text-white'
                    : isCompleted
                    ? 'bg-indigo-100 text-indigo-700'
                    : 'bg-gray-200 text-gray-500'
                }`}
              >
                {isCompleted ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  stepNum
                )}
              </div>
              <span
                className={`mt-1 text-xs font-medium ${
                  isActive ? 'text-indigo-600' : isCompleted ? 'text-indigo-500' : 'text-gray-400'
                }`}
              >
                {label}
              </span>
            </div>
            {idx < stepLabels.length - 1 && (
              <div
                className={`w-12 sm:w-20 h-0.5 mx-1 sm:mx-2 mt-[-1rem] ${
                  step > stepNum ? 'bg-indigo-400' : 'bg-gray-200'
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );

  // ── Render each step ────────────────────────────────────────────────────────

  const renderStep1 = () => (
    <div>
      <h2 className="text-lg font-semibold text-gray-900 mb-1">Select Import Type</h2>
      <p className="text-sm text-gray-500 mb-6">
        Choose the type of data you want to import into center <span className="font-medium text-gray-700">{selectedCenter?.name}</span>.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {IMPORT_TYPE_OPTIONS.map((opt) => (
          <button
            key={opt.key}
            onClick={() => handleSelectType(opt.key)}
            className="bg-white border border-gray-200 rounded-lg p-6 text-left hover:border-indigo-400 hover:shadow-md transition group focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <div className="text-indigo-600 mb-3 group-hover:text-indigo-700 transition-colors">
              {opt.icon}
            </div>
            <h3 className="font-semibold text-gray-900 mb-1">{opt.label}</h3>
            <p className="text-sm text-gray-500">{opt.description}</p>
          </button>
        ))}
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div>
      <h2 className="text-lg font-semibold text-gray-900 mb-1">Upload CSV File</h2>
      <p className="text-sm text-gray-500 mb-6">
        Upload a CSV file for <span className="font-medium text-indigo-600 capitalize">{importType}</span> import. The first row must contain column headers.
      </p>

      {/* Drag and drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
          dragOver
            ? 'border-indigo-500 bg-indigo-50'
            : file
            ? 'border-green-400 bg-green-50'
            : 'border-gray-300 hover:border-indigo-400 bg-white'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          className="hidden"
        />

        {file ? (
          <div>
            <svg className="w-12 h-12 text-green-500 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-green-700 font-medium">{file.name}</p>
            <p className="text-sm text-green-600 mt-1">
              {(file.size / 1024).toFixed(1)} KB &middot; {csvHeaders.length} columns detected &middot; Click or drag to replace
            </p>
          </div>
        ) : (
          <div>
            <svg className="w-12 h-12 text-gray-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p className="text-gray-600 font-medium">Drag and drop your CSV file here</p>
            <p className="text-sm text-gray-400 mt-1">or click to browse &middot; .csv files only &middot; max 10 MB</p>
          </div>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex items-center justify-between mt-6">
        <button
          onClick={() => { setStep(1); setFile(null); setCsvHeaders([]); setCsvPreviewRows([]); setError(null); }}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition"
        >
          Back
        </button>
        <button
          onClick={proceedToMapping}
          disabled={!file}
          className={`px-6 py-2 text-sm font-medium rounded-lg transition ${
            file
              ? 'bg-indigo-600 text-white hover:bg-indigo-700'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }`}
        >
          Continue to Mapping
        </button>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div>
      <h2 className="text-lg font-semibold text-gray-900 mb-1">Map Columns</h2>
      <p className="text-sm text-gray-500 mb-6">
        Map your CSV columns to the target fields. Fields marked with <span className="text-red-500">*</span> are required.
      </p>

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Target Field
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                CSV Column
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {fieldMappings.map((mapping) => {
              const isMapped = mapping.csvColumn !== '';
              return (
                <tr key={mapping.targetField} className="hover:bg-gray-50">
                  <td className="px-6 py-3 text-sm text-gray-900">
                    {mapping.label}
                    {mapping.required && <span className="text-red-500 ml-1">*</span>}
                  </td>
                  <td className="px-6 py-3">
                    <select
                      value={mapping.csvColumn}
                      onChange={(e) => handleMappingChange(mapping.targetField, e.target.value)}
                      className={`block w-full rounded-md border text-sm py-1.5 px-3 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${
                        mapping.required && !isMapped
                          ? 'border-red-300 bg-red-50'
                          : 'border-gray-300'
                      }`}
                    >
                      <option value="">-- Skip / Not Mapped --</option>
                      {csvHeaders.map((header) => (
                        <option key={header} value={header}>
                          {header}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-6 py-3 text-sm">
                    {isMapped ? (
                      <span className="inline-flex items-center gap-1 text-green-700">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        Mapped
                      </span>
                    ) : mapping.required ? (
                      <span className="inline-flex items-center gap-1 text-red-600">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Required
                      </span>
                    ) : (
                      <span className="text-gray-400">Optional</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Summary */}
      <div className="mt-4 flex items-center gap-4 text-sm text-gray-500">
        <span>
          {fieldMappings.filter((m) => m.csvColumn !== '').length} of {fieldMappings.length} fields mapped
        </span>
        <span>&middot;</span>
        <span>
          {fieldMappings.filter((m) => m.required && m.csvColumn === '').length} required fields remaining
        </span>
      </div>

      {/* Action buttons */}
      <div className="flex items-center justify-between mt-6">
        <button
          onClick={() => { setStep(2); setError(null); }}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition"
        >
          Back
        </button>
        <button
          onClick={proceedToPreview}
          disabled={!allRequiredMapped}
          className={`px-6 py-2 text-sm font-medium rounded-lg transition ${
            allRequiredMapped
              ? 'bg-indigo-600 text-white hover:bg-indigo-700'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }`}
        >
          Preview Import
        </button>
      </div>
    </div>
  );

  const renderStep4 = () => {
    const { headers, rows } = getMappedPreviewData();

    return (
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-1">Preview Import Data</h2>
        <p className="text-sm text-gray-500 mb-6">
          Review the first {rows.length} row{rows.length !== 1 ? 's' : ''} of mapped data before importing.
        </p>

        {rows.length === 0 ? (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
            <p className="text-yellow-700">No data rows found in the CSV file. Please check your file and try again.</p>
          </div>
        ) : (
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Row
                    </th>
                    {headers.map((h) => (
                      <th
                        key={h}
                        className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {rows.map((row, rowIdx) => (
                    <tr key={rowIdx} className="hover:bg-gray-50">
                      <td className="px-4 py-2 text-sm text-gray-400 font-mono">{rowIdx + 1}</td>
                      {row.map((cell, cellIdx) => (
                        <td key={cellIdx} className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap max-w-xs truncate">
                          {cell || <span className="text-gray-300 italic">empty</span>}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Import summary */}
        <div className="mt-4 bg-indigo-50 border border-indigo-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-indigo-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="text-sm text-indigo-800">
              <p className="font-medium">Ready to import</p>
              <p className="mt-1">
                Type: <span className="font-medium capitalize">{importType}</span> &middot;
                Center: <span className="font-medium">{selectedCenter?.name}</span> &middot;
                File: <span className="font-medium">{file?.name}</span>
              </p>
              <p className="mt-1 text-indigo-600">
                Existing records matched by parent phone + child name will be updated. New records will be created. Duplicates will be skipped.
              </p>
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center justify-between mt-6">
          <button
            onClick={() => { setStep(3); setError(null); }}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition"
          >
            Back to Mapping
          </button>
          <button
            onClick={executeImport}
            disabled={importing || rows.length === 0}
            className={`px-6 py-2 text-sm font-medium rounded-lg transition flex items-center gap-2 ${
              importing || rows.length === 0
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-indigo-600 text-white hover:bg-indigo-700'
            }`}
          >
            {importing && (
              <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            )}
            {importing ? 'Importing...' : 'Start Import'}
          </button>
        </div>
      </div>
    );
  };

  const renderStep5 = () => {
    if (!importResult) return null;

    const hasErrors = importResult.errors && importResult.errors.length > 0;
    const totalProcessed = importResult.created + importResult.updated + importResult.skipped;

    return (
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-1">Import Results</h2>
        <p className="text-sm text-gray-500 mb-6">
          Import of <span className="font-medium capitalize">{importType}</span> data has completed.
        </p>

        {/* Summary cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          <div className="bg-white border border-gray-200 rounded-lg p-4 text-center shadow-sm">
            <p className="text-2xl font-bold text-gray-900">{totalProcessed}</p>
            <p className="text-sm text-gray-500">Total Processed</p>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center shadow-sm">
            <p className="text-2xl font-bold text-green-700">{importResult.created}</p>
            <p className="text-sm text-green-600">Created</p>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center shadow-sm">
            <p className="text-2xl font-bold text-blue-700">{importResult.updated}</p>
            <p className="text-sm text-blue-600">Updated</p>
          </div>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center shadow-sm">
            <p className="text-2xl font-bold text-yellow-700">{importResult.skipped}</p>
            <p className="text-sm text-yellow-600">Skipped</p>
          </div>
        </div>

        {/* Success banner */}
        {!hasErrors && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-3">
              <svg className="w-6 h-6 text-green-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-green-800 font-medium">Import completed successfully with no errors.</p>
            </div>
          </div>
        )}

        {/* Error table */}
        {hasErrors && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-red-700 mb-2">
              Errors ({importResult.errors.length})
            </h3>
            <div className="bg-white border border-red-200 rounded-lg overflow-hidden shadow-sm">
              <div className="overflow-x-auto max-h-64 overflow-y-auto">
                <table className="min-w-full divide-y divide-red-100">
                  <thead className="bg-red-50 sticky top-0">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-red-600 uppercase">Row</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-red-600 uppercase">Field</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-red-600 uppercase">Error</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-red-50">
                    {importResult.errors.map((err, idx) => (
                      <tr key={idx} className="hover:bg-red-25">
                        <td className="px-4 py-2 text-sm text-gray-700 font-mono">{err.row}</td>
                        <td className="px-4 py-2 text-sm text-gray-700">{err.field}</td>
                        <td className="px-4 py-2 text-sm text-red-600">{err.message}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button
            onClick={resetWizard}
            className="px-6 py-2 text-sm font-medium bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
          >
            Import More Data
          </button>
          <button
            onClick={() => { setStep(1); }}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition"
          >
            Start Over
          </button>
        </div>
      </div>
    );
  };

  // ── Main render ─────────────────────────────────────────────────────────────

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">CSV Data Import</h1>
        <p className="text-sm text-gray-500 mt-1">
          Import data from Excel/CSV files into <span className="font-medium">{selectedCenter?.name}</span>
        </p>
      </div>

      {/* Step indicator */}
      {renderStepIndicator()}

      {/* Error banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-3">
            <svg className="w-5 h-5 text-red-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm text-red-700">{error}</p>
            <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Wizard steps */}
      {step === 1 && renderStep1()}
      {step === 2 && renderStep2()}
      {step === 3 && renderStep3()}
      {step === 4 && renderStep4()}
      {step === 5 && renderStep5()}
    </div>
  );
}
