'use client';

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useCenter } from '@/contexts/CenterContext';
import { getInitials, getAvatarColor } from '@/lib/utils';
import PageHeader from '@/components/ui/PageHeader';
import { Search, X, Check, AlertTriangle, Building2, CalendarCheck } from 'lucide-react';

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

export default function AttendancePage() {
  const router = useRouter();
  const { selectedCenter, loading: centerLoading } = useCenter();

  const [batches, setBatches] = useState<Batch[]>([]);
  const [selectedBatchId, setSelectedBatchId] = useState<number | null>(null);
  const [students, setStudents] = useState<StudentSummary[]>([]);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [presentIds, setPresentIds] = useState<Set<number>>(new Set());
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

  const loadStudents = useCallback(async (batchId: number) => {
    if (!selectedCenter) return;
    setLoadingStudents(true);
    setError(null);
    try {
      const data = await api.get<StudentSummary[]>(
        `/api/v1/attendance/batches/${batchId}/students?center_id=${selectedCenter.id}&session_date=${selectedDate}`
      );
      setStudents(data);
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

  const toggleSelect = (childId: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(childId)) next.delete(childId);
      else next.add(childId);
      return next;
    });
  };

  const selectAllVisible = useCallback(() => {
    const unmarked = students.filter(s => !presentIds.has(s.child_id));
    setSelectedIds(new Set(unmarked.map(s => s.child_id)));
  }, [students, presentIds]);

  const clearSelection = () => setSelectedIds(new Set());

  const markSelectedPresent = async () => {
    if (!selectedBatchId || !selectedCenter || selectedIds.size === 0 || isBulkSaving) return;
    setIsBulkSaving(true);
    setWarnings([]);
    const childIds = Array.from(selectedIds);
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

  const undoPresent = async (childId: number) => {
    if (!selectedBatchId || !selectedCenter || savingChildId) return;
    setSavingChildId(childId);
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
      setPresentIds((prev) => new Set([...prev, childId]));
      showToast(`Failed: ${err.message}`);
    } finally {
      setSavingChildId(null);
    }
  };

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

  if (centerLoading) {
    return (
      <div className="page-container">
        <div className="space-y-4">
          <div className="skeleton h-8 w-48" />
          <div className="flex gap-3">
            <div className="skeleton h-10 w-28 rounded-full" />
            <div className="skeleton h-10 w-28 rounded-full" />
            <div className="skeleton h-10 w-28 rounded-full" />
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 mt-6">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => <div key={i} className="skeleton h-24 rounded-xl" />)}
          </div>
        </div>
      </div>
    );
  }

  if (!selectedCenter) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center p-4">
        <div className="text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Building2 className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Center Selected</h3>
          <p className="text-sm text-gray-500 mb-4">Select a center to start marking attendance.</p>
          <button onClick={() => router.push('/dashboard')} className="btn-primary">
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* Toast */}
      {toast && (
        <div className="toast">
          <Check className="w-4 h-4 text-green-400" />
          {toast}
        </div>
      )}

      {/* Page header */}
      <PageHeader
        title="Attendance"
        subtitle="Select students, then mark attendance"
        action={
          <div className="flex items-center gap-3">
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="input w-auto"
            />
            {hasPresent && (
              <span className="badge-green gap-1.5">
                <Check className="w-3.5 h-3.5" />
                Saved
              </span>
            )}
          </div>
        }
      />

      {/* Warning banner */}
      {warnings.length > 0 && (
        <div className="alert-warning mb-6">
          <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1 text-sm">{warnings.map((w, i) => <p key={i}>{w}</p>)}</div>
          <button onClick={() => setWarnings([])} className="text-amber-400 hover:text-amber-600">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Batch tabs */}
      {batches.length > 0 && (
        <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-1">
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
          <button onClick={() => selectedBatchId ? loadStudents(selectedBatchId) : loadBatches()} className="btn-primary">Retry</button>
        </div>
      )}

      {/* Loading */}
      {(loadingBatches || loadingStudents) && !error && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((i) => (
            <div key={i} className="card-static p-4">
              <div className="skeleton w-10 h-10 rounded-full mx-auto mb-2" />
              <div className="skeleton h-3.5 w-20 mx-auto mb-1" />
              <div className="skeleton h-3 w-14 mx-auto" />
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
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  if (e.target.value.length >= 2) setActiveLetter(null);
                }}
                placeholder="Search by child name..."
                className="input pl-9 pr-8"
              />
              {searchQuery && (
                <button onClick={() => setSearchQuery('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span>{students.length} enrolled</span>
              <span className="text-emerald-600 font-medium">{presentStudents.length} present</span>
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
            <div className="mb-4 alert-info justify-between">
              <span className="text-sm font-medium">
                {selectedIds.size} student{selectedIds.size > 1 ? 's' : ''} selected
              </span>
              <div className="flex items-center gap-2">
                <button onClick={clearSelection} className="btn-secondary btn-sm">
                  Clear
                </button>
                <button
                  onClick={markSelectedPresent}
                  disabled={isBulkSaving}
                  className="btn-success btn-sm"
                >
                  {isBulkSaving ? (
                    <div className="spinner-sm" />
                  ) : (
                    <Check className="w-4 h-4" />
                  )}
                  Mark Attendance
                </button>
              </div>
            </div>
          )}

          {/* Select All link */}
          {filteredStudents.length > 0 && selectedIds.size === 0 && (
            <div className="mb-3 flex justify-end">
              <button onClick={selectAllVisible} className="text-xs text-blue-600 hover:text-blue-800 font-medium">
                Select All ({unmarkedStudents.length})
              </button>
            </div>
          )}

          {/* Student cards grid */}
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
                    {isSelected && (
                      <div className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center shadow-sm">
                        <Check className="w-3 h-3 text-white" strokeWidth={3} />
                      </div>
                    )}
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-bold mx-auto mb-2 ${color} ${isSelected ? 'ring-2 ring-blue-400 ring-offset-2' : 'group-hover:ring-2 group-hover:ring-blue-300 group-hover:ring-offset-2'} transition-all`}>
                      {initials}
                    </div>
                    <div className="text-sm font-medium text-gray-900 truncate">{student.child_name}</div>
                    <div className="text-xs text-gray-400 mt-0.5">#{student.enrollment_id}</div>
                    <div className="mt-2 flex items-center justify-center gap-1.5">
                      <span className="text-[10px] text-gray-400">{student.classes_attended}/{student.classes_booked}</span>
                      {isLow && <span className="badge-yellow text-[10px] px-1.5 py-0.5">{student.classes_remaining} left</span>}
                    </div>
                  </button>
                );
              })}
            </div>
          )}

          {/* Present Today */}
          {presentStudents.length > 0 && (
            <div className="mt-8">
              <div className="flex items-center gap-3 mb-4">
                <h2 className="text-sm font-semibold text-gray-900">Present Today</h2>
                <span className="badge-green">
                  {presentStudents.length} / {students.length}
                </span>
                <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all duration-500"
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
                      className="rounded-xl p-4 text-center transition-all relative bg-emerald-50 border border-emerald-200"
                    >
                      <div className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-emerald-500 rounded-full flex items-center justify-center shadow-sm">
                        <Check className="w-3 h-3 text-white" strokeWidth={3} />
                      </div>
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-bold mx-auto mb-2 ${color} ring-2 ring-emerald-400 ring-offset-2`}>
                        {initials}
                      </div>
                      <div className="text-sm font-medium text-emerald-900 truncate">{student.child_name}</div>
                      <div className="text-xs text-emerald-500 mt-0.5">#{student.enrollment_id}</div>
                      <button
                        onClick={() => undoPresent(student.child_id)}
                        disabled={isSaving}
                        className="mt-2 text-xs text-emerald-600 hover:text-red-500 transition disabled:opacity-50 font-medium"
                        title="Undo"
                      >
                        {isSaving ? (
                          <div className="spinner-sm inline-block" />
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
          <CalendarCheck className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No batches found for this center.</p>
        </div>
      )}
    </div>
  );
}
