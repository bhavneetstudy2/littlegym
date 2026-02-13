'use client';

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useCenter } from '@/contexts/CenterContext';

interface Batch {
  id: number;
  name: string;
  age_min: number | null;
  age_max: number | null;
  days_of_week: string[] | null;
  start_time: string | null;
  end_time: string | null;
  capacity: number | null;
}

interface StudentSummary {
  child_id: number;
  child_name: string;
  enrollment_id: number;
  batch_id: number;
  batch_name: string;
  classes_booked: number;
  classes_attended: number;
  classes_remaining: number;
  last_attendance_date: string | null;
  enrollment_status: string;
  is_present_today: boolean | null;
}

interface AttendanceResponse {
  id: number;
  child_id: number;
  status: string;
  visit_warning: string | null;
}

const ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  return name.slice(0, 2).toUpperCase();
}

function getAvatarColor(name: string): string {
  const colors = [
    'bg-violet-600', 'bg-emerald-600', 'bg-blue-600', 'bg-amber-600',
    'bg-rose-600', 'bg-cyan-600', 'bg-indigo-600', 'bg-teal-600',
    'bg-orange-600', 'bg-pink-600', 'bg-lime-700', 'bg-fuchsia-600',
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  return colors[Math.abs(hash) % colors.length];
}

export default function AttendancePage() {
  const router = useRouter();
  const { selectedCenter, loading: centerLoading } = useCenter();

  const [batches, setBatches] = useState<Batch[]>([]);
  const [selectedBatchId, setSelectedBatchId] = useState<number | null>(null);
  const [students, setStudents] = useState<StudentSummary[]>([]);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  // Present tracking - seeded from API
  const [presentIds, setPresentIds] = useState<Set<number>>(new Set());
  // Selected cards awaiting bulk mark
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [isBulkSaving, setIsBulkSaving] = useState(false);

  const [searchQuery, setSearchQuery] = useState('');
  const [activeLetter, setActiveLetter] = useState<string | null>(null);
  const [loadingBatches, setLoadingBatches] = useState(false);
  const [loadingStudents, setLoadingStudents] = useState(false);
  const [savingChildId, setSavingChildId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [toast, setToast] = useState<string | null>(null);

  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showToast = useCallback((msg: string) => {
    setToast(msg);
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 2000);
  }, []);

  // Load batches
  const loadBatches = useCallback(async () => {
    if (!selectedCenter) return;
    setLoadingBatches(true);
    setError(null);
    try {
      const data = await api.get<Batch[]>(
        `/api/v1/enrollments/batches?center_id=${selectedCenter.id}`
      );
      setBatches(data);
      if (data.length > 0 && !selectedBatchId) {
        setSelectedBatchId(data[0].id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load batches');
    } finally {
      setLoadingBatches(false);
    }
  }, [selectedCenter]);

  useEffect(() => {
    if (selectedCenter) loadBatches();
  }, [selectedCenter, loadBatches]);

  // Load students + existing attendance in ONE call (was 3 sequential calls before)
  const loadStudents = useCallback(async (batchId: number) => {
    if (!selectedCenter) return;
    setLoadingStudents(true);
    setError(null);
    try {
      // Single API call: students + attendance status via session_date param
      // Backend also excludes exhausted students by default
      const data = await api.get<StudentSummary[]>(
        `/api/v1/attendance/batches/${batchId}/students?center_id=${selectedCenter.id}&session_date=${selectedDate}`
      );
      setStudents(data);

      // Build presentIds from is_present_today field returned by backend
      const alreadyPresent = new Set<number>();
      data.forEach((s) => {
        if (s.is_present_today) alreadyPresent.add(s.child_id);
      });
      setPresentIds(alreadyPresent);
      setSelectedIds(new Set());
    } catch (err: any) {
      setError(err.message || 'Failed to load students');
    } finally {
      setLoadingStudents(false);
    }
  }, [selectedCenter, selectedDate]);

  useEffect(() => {
    if (selectedBatchId && selectedCenter) {
      loadStudents(selectedBatchId);
      setSearchQuery('');
      setActiveLetter(null);
      setSelectedIds(new Set());
    }
  }, [selectedBatchId, selectedCenter, selectedDate, loadStudents]);

  // Toggle selection of a student card
  const toggleSelect = (childId: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(childId)) next.delete(childId);
      else next.add(childId);
      return next;
    });
  };

  // Select all visible unmarked students (uses unmarkedStudents since filteredStudents computed later)
  const selectAllVisible = useCallback(() => {
    const unmarked = students.filter(s => !presentIds.has(s.child_id));
    setSelectedIds(new Set(unmarked.map(s => s.child_id)));
  }, [students, presentIds]);

  // Clear selection
  const clearSelection = () => setSelectedIds(new Set());

  // Bulk mark selected students as present
  const markSelectedPresent = async () => {
    if (!selectedBatchId || !selectedCenter || selectedIds.size === 0 || isBulkSaving) return;
    setIsBulkSaving(true);
    setWarnings([]);

    const childIds = Array.from(selectedIds);

    // Optimistic: move all selected to present
    setPresentIds((prev) => new Set([...prev, ...childIds]));

    try {
      const results = await api.post<AttendanceResponse[]>(
        `/api/v1/attendance/quick-mark?center_id=${selectedCenter.id}`,
        {
          batch_id: selectedBatchId,
          session_date: selectedDate,
          attendances: childIds.map(id => ({ child_id: id, status: 'PRESENT', notes: null })),
        }
      );
      showToast(`${childIds.length} student${childIds.length > 1 ? 's' : ''} marked present`);

      // Check for warnings
      const newWarnings: string[] = [];
      results.forEach((r) => {
        if (r.visit_warning) {
          const student = students.find(s => s.child_id === r.child_id);
          newWarnings.push(`${student?.child_name || 'Student'}: ${r.visit_warning}`);
        }
      });
      if (newWarnings.length > 0) setWarnings(prev => [...prev, ...newWarnings]);

      setSelectedIds(new Set());
    } catch (err: any) {
      // Rollback
      setPresentIds((prev) => {
        const next = new Set(prev);
        childIds.forEach(id => next.delete(id));
        return next;
      });
      showToast(`Failed: ${err.message}`);
    } finally {
      setIsBulkSaving(false);
    }
  };

  // Undo attendance - deletes record on backend, decrements visits_used
  const undoPresent = async (childId: number) => {
    if (!selectedBatchId || !selectedCenter || savingChildId) return;
    setSavingChildId(childId);

    // Optimistic: immediately remove from present
    setPresentIds((prev) => { const next = new Set(prev); next.delete(childId); return next; });

    try {
      await api.post<AttendanceResponse[]>(
        `/api/v1/attendance/quick-mark?center_id=${selectedCenter.id}`,
        {
          batch_id: selectedBatchId,
          session_date: selectedDate,
          attendances: [{ child_id: childId, status: 'ABSENT', notes: 'Undo' }],
        }
      );
      const student = students.find((s) => s.child_id === childId);
      showToast(`${student?.child_name || 'Student'} removed`);
    } catch (err: any) {
      // Rollback: put back into present
      setPresentIds((prev) => new Set([...prev, childId]));
      showToast(`Failed: ${err.message}`);
    } finally {
      setSavingChildId(null);
    }
  };

  // Derived - exhausted already excluded by backend
  const unmarkedStudents = useMemo(() => students.filter((s) => !presentIds.has(s.child_id)), [students, presentIds]);
  const presentStudents = useMemo(() => students.filter((s) => presentIds.has(s.child_id)), [students, presentIds]);

  const filteredStudents = useMemo(() => {
    let list = unmarkedStudents;
    if (activeLetter) list = list.filter((s) => s.child_name.toUpperCase().startsWith(activeLetter!));
    if (searchQuery.length >= 2) {
      const q = searchQuery.toLowerCase();
      list = list.filter((s) => s.child_name.toLowerCase().includes(q) || String(s.enrollment_id).includes(q));
    }
    return list;
  }, [unmarkedStudents, activeLetter, searchQuery]);

  const activeLetters = useMemo(() => {
    const letters = new Set<string>();
    unmarkedStudents.forEach((s) => {
      const ch = s.child_name.charAt(0).toUpperCase();
      if (ch >= 'A' && ch <= 'Z') letters.add(ch);
    });
    return letters;
  }, [unmarkedStudents]);

  const hasPresent = presentIds.size > 0;

  // --- RENDER ---

  if (centerLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-48" />
          <div className="flex gap-3"><div className="h-10 bg-gray-200 rounded-full w-28" /><div className="h-10 bg-gray-200 rounded-full w-28" /><div className="h-10 bg-gray-200 rounded-full w-28" /></div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 mt-6">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => <div key={i} className="h-20 bg-gray-200 rounded-xl" />)}
          </div>
        </div>
      </div>
    );
  }

  if (!selectedCenter) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center p-4">
        <div className="text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Center Selected</h3>
          <p className="text-gray-500 mb-4">Select a center to start marking attendance.</p>
          <button onClick={() => router.push('/dashboard')} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm font-medium">
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-6">
      {/* Toast */}
      {toast && (
        <div className="fixed top-4 right-4 z-50 bg-gray-900 text-white text-sm px-4 py-2.5 rounded-lg shadow-lg flex items-center gap-2">
          <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
          {toast}
        </div>
      )}

      {/* Page header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <h1 className="text-xl lg:text-2xl font-bold text-gray-900">Attendance</h1>
          <p className="text-sm text-gray-500 mt-0.5">Select students, then mark attendance</p>
        </div>
        <div className="flex items-center gap-3">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
          />
          {hasPresent && (
            <div className="flex items-center gap-1.5 bg-green-100 text-green-700 px-3 py-1.5 rounded-full text-xs font-semibold">
              <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
              Saved
            </div>
          )}
        </div>
      </div>

      {/* Warning banner */}
      {warnings.length > 0 && (
        <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start justify-between gap-2">
          <div className="flex items-start gap-2">
            <svg className="w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <div className="text-sm text-amber-700">{warnings.map((w, i) => <p key={i}>{w}</p>)}</div>
          </div>
          <button onClick={() => setWarnings([])} className="text-amber-400 hover:text-amber-600 mt-0.5">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
      )}

      {/* Batch tabs */}
      {batches.length > 0 && (
        <div className="flex items-center gap-2 mb-5 overflow-x-auto pb-1">
          {batches.map((b) => {
            const isActive = b.id === selectedBatchId;
            return (
              <button
                key={b.id}
                onClick={() => setSelectedBatchId(b.id)}
                className={`flex-shrink-0 px-4 py-2 rounded-full text-sm font-medium transition whitespace-nowrap ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'bg-white text-gray-600 border border-gray-200 hover:border-blue-300 hover:text-blue-600'
                }`}
              >
                {b.name}
              </button>
            );
          })}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="text-center py-12">
          <p className="text-red-600 text-sm mb-3">{error}</p>
          <button onClick={() => selectedBatchId ? loadStudents(selectedBatchId) : loadBatches()} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">Retry</button>
        </div>
      )}

      {/* Loading */}
      {(loadingBatches || loadingStudents) && !error && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((i) => (
            <div key={i} className="animate-pulse bg-white rounded-xl border border-gray-100 p-4">
              <div className="w-11 h-11 bg-gray-200 rounded-full mx-auto mb-2" />
              <div className="h-3.5 bg-gray-200 rounded w-20 mx-auto mb-1" />
              <div className="h-3 bg-gray-200 rounded w-14 mx-auto" />
            </div>
          ))}
        </div>
      )}

      {/* Main content */}
      {selectedBatchId && !loadingBatches && !loadingStudents && !error && (
        <>
          {/* Search + filter row */}
          <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-4">
            <div className="relative flex-1 sm:max-w-sm">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  if (e.target.value.length >= 2) setActiveLetter(null);
                }}
                placeholder="Search by child name..."
                className="w-full pl-9 pr-8 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none bg-white"
              />
              {searchQuery && (
                <button onClick={() => setSearchQuery('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              )}
            </div>
            {/* Stats on right */}
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span>{students.length} enrolled</span>
              <span className="text-green-600 font-medium">{presentStudents.length} present</span>
              <span>{unmarkedStudents.length} remaining</span>
            </div>
          </div>

          {/* Alphabet filter */}
          <div className="flex flex-wrap gap-1 mb-4">
            <button
              onClick={() => setActiveLetter(null)}
              className={`px-2.5 py-1 rounded text-xs font-medium transition ${
                !activeLetter ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              All
            </button>
            {ALPHABET.filter((l) => activeLetters.has(l)).map((letter) => (
              <button
                key={letter}
                onClick={() => {
                  setActiveLetter(activeLetter === letter ? null : letter);
                  if (activeLetter !== letter) setSearchQuery('');
                }}
                className={`px-2.5 py-1 rounded text-xs font-medium transition ${
                  activeLetter === letter
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {letter}
              </button>
            ))}
          </div>

          {/* Selection action bar */}
          {selectedIds.size > 0 && (
            <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-center justify-between">
              <span className="text-sm font-medium text-blue-800">
                {selectedIds.size} student{selectedIds.size > 1 ? 's' : ''} selected
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={clearSelection}
                  className="px-3 py-1.5 text-sm text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Clear
                </button>
                <button
                  onClick={markSelectedPresent}
                  disabled={isBulkSaving}
                  className="px-4 py-1.5 text-sm font-semibold text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {isBulkSaving ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                  )}
                  Mark Attendance
                </button>
              </div>
            </div>
          )}

          {/* Select All / Clear link */}
          {filteredStudents.length > 0 && selectedIds.size === 0 && (
            <div className="mb-3 flex justify-end">
              <button onClick={selectAllVisible} className="text-xs text-blue-600 hover:text-blue-800 font-medium">
                Select All ({unmarkedStudents.length})
              </button>
            </div>
          )}

          {/* Student cards grid - unmarked (tap to select) */}
          {filteredStudents.length === 0 ? (
            <div className="text-center py-16">
              <p className="text-gray-400">
                {unmarkedStudents.length === 0
                  ? students.length === 0
                    ? 'No active students in this batch'
                    : 'All students marked present!'
                  : searchQuery.length >= 2
                    ? `No matches for "${searchQuery}"`
                    : activeLetter
                      ? `No unmarked students starting with "${activeLetter}"`
                      : 'No students to show'}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
              {filteredStudents.map((student) => {
                const initials = getInitials(student.child_name);
                const color = getAvatarColor(student.child_name);
                const isLow = student.classes_remaining > 0 && student.classes_remaining <= 3;
                const isSelected = selectedIds.has(student.child_id);

                return (
                  <button
                    key={student.child_id}
                    onClick={() => toggleSelect(student.child_id)}
                    className={`rounded-xl border p-4 text-center active:scale-[0.97] transition-all group relative ${
                      isSelected
                        ? 'bg-blue-50 border-2 border-blue-500 shadow-sm shadow-blue-100'
                        : 'bg-white border-gray-200 hover:border-blue-400 hover:shadow-md'
                    }`}
                  >
                    {/* Selection checkmark */}
                    {isSelected && (
                      <div className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center shadow-sm">
                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                      </div>
                    )}
                    <div className={`w-11 h-11 rounded-full flex items-center justify-center text-white text-sm font-bold mx-auto mb-2 ${color} ${isSelected ? 'ring-2 ring-blue-400 ring-offset-2' : 'group-hover:ring-2 group-hover:ring-blue-300 group-hover:ring-offset-2'} transition-all`}>
                      {initials}
                    </div>
                    <div className="text-sm font-medium text-gray-900 truncate">{student.child_name}</div>
                    <div className="text-xs text-gray-400 mt-0.5">#{student.enrollment_id}</div>
                    <div className="mt-2 flex items-center justify-center gap-1.5">
                      <span className="text-[10px] text-gray-400">{student.classes_attended}/{student.classes_booked}</span>
                      {isLow && <span className="text-[10px] bg-amber-100 text-amber-600 px-1.5 py-0.5 rounded font-medium">{student.classes_remaining} left</span>}
                    </div>
                  </button>
                );
              })}
            </div>
          )}

          {/* Present Today - green tiles with checkmark */}
          {presentStudents.length > 0 && (
            <div className="mt-6">
              <div className="flex items-center gap-3 mb-3">
                <h2 className="text-sm font-semibold text-gray-900">Present Today</h2>
                <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">
                  {presentStudents.length} / {students.length}
                </span>
                <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500 rounded-full transition-all duration-500"
                    style={{ width: `${students.length > 0 ? (presentStudents.length / students.length) * 100 : 0}%` }}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
                {presentStudents.map((student) => {
                  const isSaving = savingChildId === student.child_id;
                  const initials = getInitials(student.child_name);
                  const color = getAvatarColor(student.child_name);
                  return (
                    <div
                      key={student.child_id}
                      className="rounded-xl p-4 text-center transition-all relative bg-green-50 border border-green-200"
                    >
                      {/* Green checkmark badge */}
                      <div className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-green-500 rounded-full flex items-center justify-center shadow-sm">
                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={3}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                      </div>
                      {/* Avatar with green ring */}
                      <div className={`w-11 h-11 rounded-full flex items-center justify-center text-white text-sm font-bold mx-auto mb-2 ${color} ring-2 ring-green-400 ring-offset-2`}>
                        {initials}
                      </div>
                      <div className="text-sm font-medium text-green-900 truncate">{student.child_name}</div>
                      <div className="text-xs text-green-500 mt-0.5">#{student.enrollment_id}</div>
                      {/* Undo button */}
                      <button
                        onClick={() => undoPresent(student.child_id)}
                        disabled={isSaving}
                        className="mt-2 text-xs text-green-600 hover:text-red-500 transition disabled:opacity-50 font-medium"
                        title="Undo"
                      >
                        {isSaving ? (
                          <div className="w-3.5 h-3.5 border-2 border-green-400 border-t-transparent rounded-full animate-spin inline-block" />
                        ) : (
                          'Undo'
                        )}
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}

      {/* No batches */}
      {!loadingBatches && batches.length === 0 && !error && (
        <div className="text-center py-20">
          <svg className="mx-auto w-12 h-12 text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p className="text-gray-500">No batches found for this center.</p>
        </div>
      )}
    </div>
  );
}
