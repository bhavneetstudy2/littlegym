'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { api } from '@/lib/api';
import { useCenter } from '@/contexts/CenterContext';
import type {
  Batch, Curriculum, ActivityCategory, ProgressionLevel,
  WeeklyProgressResponse, WeeklyProgressBulkPayload, WeeklyProgressEntry,
  BatchStudentProgressSummary, ChildTrainerNotes,
} from '@/types';

// ── Helpers ──

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

function computeWeekNumber(enrollmentStartDate: string | null): number {
  if (!enrollmentStartDate) return 1;
  const start = new Date(enrollmentStartDate);
  const today = new Date();
  const diffDays = Math.floor((today.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
  return Math.max(1, Math.ceil(diffDays / 7));
}

function weekStartDate(enrollmentStartDate: string | null, weekNumber: number): string {
  if (!enrollmentStartDate) return new Date().toISOString().split('T')[0];
  const start = new Date(enrollmentStartDate);
  const offset = (weekNumber - 1) * 7;
  const d = new Date(start.getTime() + offset * 24 * 60 * 60 * 1000);
  return d.toISOString().split('T')[0];
}

function weekDateRange(enrollmentStartDate: string | null, weekNumber: number): string {
  if (!enrollmentStartDate) return '';
  const start = new Date(enrollmentStartDate);
  const startOffset = (weekNumber - 1) * 7;
  const weekStart = new Date(start.getTime() + startOffset * 24 * 60 * 60 * 1000);
  const weekEnd = new Date(weekStart.getTime() + 6 * 24 * 60 * 60 * 1000);
  const fmt = (d: Date) => d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
  return `${fmt(weekStart)} - ${fmt(weekEnd)}`;
}

// ── Main Component ──

export default function ProgressPage() {
  const { selectedCenter } = useCenter();
  const centerParam = selectedCenter ? `center_id=${selectedCenter.id}` : '';

  // Batch & curriculum selection
  const [batches, setBatches] = useState<Batch[]>([]);
  const [selectedBatchId, setSelectedBatchId] = useState<number | null>(null);
  const [curricula, setCurricula] = useState<Curriculum[]>([]);
  const [selectedCurriculumId, setSelectedCurriculumId] = useState<number | null>(null);
  const [activityCategories, setActivityCategories] = useState<ActivityCategory[]>([]);

  // Student list
  const [students, setStudents] = useState<BatchStudentProgressSummary[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loadingStudents, setLoadingStudents] = useState(false);

  // Selected student progress sheet
  const [selectedStudent, setSelectedStudent] = useState<BatchStudentProgressSummary | null>(null);
  const [weekNumber, setWeekNumber] = useState(1);
  const [weekProgress, setWeekProgress] = useState<Record<number, WeeklyProgressEntry>>({});
  const [trainerNotes, setTrainerNotes] = useState<ChildTrainerNotes | null>(null);
  const [parentExpectation, setParentExpectation] = useState('');
  const [progressCheck, setProgressCheck] = useState('');
  const [saving, setSaving] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(false);

  // UI state
  const [loadingBatches, setLoadingBatches] = useState(true);
  const [toast, setToast] = useState<string | null>(null);

  // Show toast
  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  };

  // ── Load batches & curricula ──
  useEffect(() => {
    if (!selectedCenter) return;
    const load = async () => {
      setLoadingBatches(true);
      try {
        const [batchData, currData] = await Promise.all([
          api.get<Batch[]>(`/api/v1/batches?${centerParam}`),
          api.get<Curriculum[]>('/api/v1/curriculum'),
        ]);
        setBatches(batchData.filter(b => b.active));
        setCurricula(currData);
        if (batchData.length > 0 && !selectedBatchId) {
          setSelectedBatchId(batchData[0].id);
        }
        // Auto-select first curriculum
        if (currData.length > 0 && !selectedCurriculumId) {
          setSelectedCurriculumId(currData[0].id);
        }
      } catch (err) {
        console.error('Failed to load batches/curricula:', err);
      } finally {
        setLoadingBatches(false);
      }
    };
    load();
  }, [selectedCenter]);

  // ── Load activity categories when curriculum changes ──
  useEffect(() => {
    if (!selectedCurriculumId) return;
    const load = async () => {
      try {
        const data = await api.get<ActivityCategory[]>(
          `/api/v1/progress/activity-categories?curriculum_id=${selectedCurriculumId}`
        );
        setActivityCategories(data);
      } catch (err) {
        console.error('Failed to load activity categories:', err);
      }
    };
    load();
  }, [selectedCurriculumId]);

  // ── Load students when batch or curriculum changes ──
  useEffect(() => {
    if (!selectedBatchId || !selectedCurriculumId || !selectedCenter) return;
    const load = async () => {
      setLoadingStudents(true);
      try {
        const data = await api.get<BatchStudentProgressSummary[]>(
          `/api/v1/progress/batch-summary/${selectedBatchId}?curriculum_id=${selectedCurriculumId}&${centerParam}`
        );
        setStudents(data);
      } catch (err) {
        console.error('Failed to load students:', err);
        setStudents([]);
      } finally {
        setLoadingStudents(false);
      }
    };
    load();
  }, [selectedBatchId, selectedCurriculumId, selectedCenter]);

  // ── Load weekly progress when student or week changes ──
  const loadStudentProgress = useCallback(async (student: BatchStudentProgressSummary, week: number) => {
    setLoadingProgress(true);
    try {
      const [progressData, notesData] = await Promise.all([
        api.get<WeeklyProgressResponse[]>(
          `/api/v1/progress/weekly/${student.child_id}?week_number=${week}&enrollment_id=${student.enrollment_id || ''}&${centerParam}`
        ),
        api.get<ChildTrainerNotes | null>(
          `/api/v1/progress/trainer-notes/${student.child_id}?enrollment_id=${student.enrollment_id || ''}&${centerParam}`
        ),
      ]);

      // Build progress map: activity_category_id → entry
      const map: Record<number, WeeklyProgressEntry> = {};
      for (const p of progressData) {
        map[p.activity_category_id] = {
          activity_category_id: p.activity_category_id,
          progression_level_id: p.progression_level_id,
          numeric_value: p.numeric_value,
          notes: p.notes,
        };
      }
      setWeekProgress(map);
      setTrainerNotes(notesData);
      setParentExpectation(notesData?.parent_expectation || '');
      setProgressCheck(notesData?.progress_check || '');
    } catch (err) {
      console.error('Failed to load progress:', err);
    } finally {
      setLoadingProgress(false);
    }
  }, [centerParam]);

  // ── Open student sheet ──
  const openStudentSheet = (student: BatchStudentProgressSummary) => {
    setSelectedStudent(student);
    const week = student.current_week;
    setWeekNumber(week);
    loadStudentProgress(student, week);
  };

  // ── Navigate weeks ──
  const changeWeek = (delta: number) => {
    if (!selectedStudent) return;
    const newWeek = Math.max(1, weekNumber + delta);
    setWeekNumber(newWeek);
    loadStudentProgress(selectedStudent, newWeek);
  };

  // ── Update a single activity in local state ──
  const updateLocalProgress = (activityCategoryId: number, updates: Partial<WeeklyProgressEntry>) => {
    setWeekProgress(prev => ({
      ...prev,
      [activityCategoryId]: {
        activity_category_id: activityCategoryId,
        progression_level_id: prev[activityCategoryId]?.progression_level_id ?? null,
        numeric_value: prev[activityCategoryId]?.numeric_value ?? null,
        notes: prev[activityCategoryId]?.notes ?? null,
        ...updates,
      },
    }));
  };

  // ── Save ──
  const handleSave = async () => {
    if (!selectedStudent) return;
    setSaving(true);
    try {
      const entries: WeeklyProgressEntry[] = activityCategories.map(cat => ({
        activity_category_id: cat.id,
        progression_level_id: weekProgress[cat.id]?.progression_level_id ?? null,
        numeric_value: weekProgress[cat.id]?.numeric_value ?? null,
        notes: weekProgress[cat.id]?.notes ?? null,
      }));

      const payload: WeeklyProgressBulkPayload = {
        child_id: selectedStudent.child_id,
        enrollment_id: selectedStudent.enrollment_id,
        week_number: weekNumber,
        week_start_date: weekStartDate(selectedStudent.enrollment_start_date, weekNumber),
        entries,
      };

      await api.post(`/api/v1/progress/weekly/bulk-update?${centerParam}`, payload);

      // Save trainer notes
      await api.post(`/api/v1/progress/trainer-notes?${centerParam}`, {
        child_id: selectedStudent.child_id,
        enrollment_id: selectedStudent.enrollment_id,
        parent_expectation: parentExpectation,
        progress_check: progressCheck,
      });

      showToast(`Week ${weekNumber} saved for ${selectedStudent.child_name}`);

      // Refresh student summary
      if (selectedBatchId && selectedCurriculumId) {
        const data = await api.get<BatchStudentProgressSummary[]>(
          `/api/v1/progress/batch-summary/${selectedBatchId}?curriculum_id=${selectedCurriculumId}&${centerParam}`
        );
        setStudents(data);
      }
    } catch (err) {
      console.error('Failed to save:', err);
      showToast('Failed to save progress');
    } finally {
      setSaving(false);
    }
  };

  // ── Filtered students ──
  const filteredStudents = useMemo(() => {
    if (!searchQuery) return students;
    const q = searchQuery.toLowerCase();
    return students.filter(s => s.child_name.toLowerCase().includes(q));
  }, [students, searchQuery]);

  // ── Group activities by category_group ──
  const groupedActivities = useMemo(() => {
    const groups: Record<string, ActivityCategory[]> = {};
    for (const cat of activityCategories) {
      const group = cat.category_group || 'Other';
      if (!groups[group]) groups[group] = [];
      groups[group].push(cat);
    }
    return groups;
  }, [activityCategories]);

  // ── Loading State ──
  if (loadingBatches) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Progress Tracker</h1>
          <p className="text-gray-600">Track weekly student progress</p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="bg-white rounded-xl p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
              <div className="h-3 bg-gray-200 rounded w-1/2" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!selectedCenter) {
    return (
      <div className="p-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-yellow-800">
          Please select a center to view progress tracking.
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Progress Tracker</h1>
          <p className="text-gray-600">Track weekly student progress across activities</p>
        </div>
        {/* Curriculum selector */}
        <select
          value={selectedCurriculumId || ''}
          onChange={e => setSelectedCurriculumId(Number(e.target.value))}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
        >
          {curricula.map(c => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      {/* Batch Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {batches.map(batch => (
          <button
            key={batch.id}
            onClick={() => { setSelectedBatchId(batch.id); setSelectedStudent(null); }}
            className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition ${
              selectedBatchId === batch.id
                ? 'bg-blue-600 text-white shadow-md'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            {batch.name}
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search student by name..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          className="w-full md:w-80 px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Student Grid + Progress Sheet side by side */}
      <div className="flex gap-6">
        {/* Student Cards */}
        <div className={`${selectedStudent ? 'w-1/3' : 'w-full'} transition-all duration-300`}>
          {loadingStudents ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="bg-white rounded-xl p-4 animate-pulse border border-gray-200">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gray-200 rounded-full" />
                    <div>
                      <div className="h-4 bg-gray-200 rounded w-24 mb-1" />
                      <div className="h-3 bg-gray-200 rounded w-16" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : filteredStudents.length === 0 ? (
            <div className="bg-white rounded-xl p-8 text-center text-gray-500 border border-gray-200">
              {students.length === 0
                ? 'No enrolled students in this batch'
                : 'No students matching search'}
            </div>
          ) : (
            <div className={`grid ${selectedStudent ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'} gap-3`}>
              {filteredStudents.map(student => {
                const isSelected = selectedStudent?.child_id === student.child_id;
                const pct = student.total_activities > 0
                  ? Math.round((student.completed_activities / student.total_activities) * 100)
                  : 0;

                return (
                  <button
                    key={student.child_id}
                    onClick={() => openStudentSheet(student)}
                    className={`w-full text-left rounded-xl p-4 transition border ${
                      isSelected
                        ? 'bg-blue-50 border-blue-400 ring-2 ring-blue-200'
                        : 'bg-white border-gray-200 hover:border-blue-300 hover:shadow-sm'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-bold ${getAvatarColor(student.child_name)}`}>
                        {getInitials(student.child_name)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-gray-900 truncate">{student.child_name}</div>
                        <div className="text-xs text-gray-500">
                          Week {student.current_week}
                          {student.latest_recorded_week
                            ? ` (recorded till Wk ${student.latest_recorded_week})`
                            : ' (no records yet)'}
                        </div>
                      </div>
                    </div>
                    {/* Progress bar */}
                    <div className="mt-3">
                      <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                        <span>{student.completed_activities}/{student.total_activities} activities</span>
                        <span>{pct}%</span>
                      </div>
                      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            pct >= 80 ? 'bg-green-500' : pct >= 40 ? 'bg-blue-500' : pct > 0 ? 'bg-amber-500' : 'bg-gray-300'
                          }`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Progress Sheet (right panel) */}
        {selectedStudent && (
          <div className="w-2/3 bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            {/* Sheet header */}
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-gray-900">{selectedStudent.child_name}</h2>
                  <p className="text-sm text-gray-500">
                    Week {weekNumber} &middot; {weekDateRange(selectedStudent.enrollment_start_date, weekNumber)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => changeWeek(-1)}
                    disabled={weekNumber <= 1 || loadingProgress}
                    className="px-3 py-1.5 text-sm bg-gray-200 rounded-lg hover:bg-gray-300 disabled:opacity-40 transition"
                  >
                    &larr; Wk {weekNumber - 1}
                  </button>
                  <span className="text-sm font-bold text-blue-600 min-w-[50px] text-center">Wk {weekNumber}</span>
                  <button
                    onClick={() => changeWeek(1)}
                    disabled={loadingProgress}
                    className="px-3 py-1.5 text-sm bg-gray-200 rounded-lg hover:bg-gray-300 disabled:opacity-40 transition"
                  >
                    Wk {weekNumber + 1} &rarr;
                  </button>
                  <button
                    onClick={() => setSelectedStudent(null)}
                    className="ml-2 text-gray-400 hover:text-gray-600 text-xl"
                    title="Close"
                  >
                    &times;
                  </button>
                </div>
              </div>
            </div>

            {loadingProgress ? (
              <div className="p-8 text-center text-gray-500">Loading progress...</div>
            ) : (
              <div className="overflow-y-auto" style={{ maxHeight: 'calc(100vh - 320px)' }}>
                {/* Trainer Notes */}
                <div className="p-5 border-b border-gray-200 bg-blue-50/50">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Parent Expectation</label>
                      <textarea
                        value={parentExpectation}
                        onChange={e => setParentExpectation(e.target.value)}
                        rows={2}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 resize-none"
                        placeholder="What does the parent expect?"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Progress Check</label>
                      <textarea
                        value={progressCheck}
                        onChange={e => setProgressCheck(e.target.value)}
                        rows={2}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 resize-none"
                        placeholder="Trainer's assessment this week"
                      />
                    </div>
                  </div>
                </div>

                {/* Activities grouped */}
                {Object.entries(groupedActivities).map(([groupName, categories]) => (
                  <div key={groupName}>
                    <div className="px-5 py-2 bg-gray-100 border-b border-gray-200">
                      <h3 className="text-xs font-bold text-gray-600 uppercase tracking-wider">{groupName}</h3>
                    </div>
                    {categories.map(cat => {
                      const entry = weekProgress[cat.id];
                      const isLevel = cat.measurement_type === 'LEVEL';

                      return (
                        <div key={cat.id} className="px-5 py-3 border-b border-gray-100 hover:bg-gray-50">
                          <div className="flex items-center justify-between gap-4">
                            <div className="flex-shrink-0 w-36">
                              <span className="text-sm font-medium text-gray-900">{cat.name}</span>
                            </div>

                            {isLevel ? (
                              <select
                                value={entry?.progression_level_id ?? ''}
                                onChange={e => updateLocalProgress(cat.id, {
                                  progression_level_id: e.target.value ? Number(e.target.value) : null,
                                })}
                                className={`flex-1 px-3 py-1.5 text-sm border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                                  entry?.progression_level_id ? 'border-blue-400 bg-blue-50' : 'border-gray-300'
                                }`}
                              >
                                <option value="">-- Not assessed --</option>
                                {cat.progression_levels.map(level => (
                                  <option key={level.id} value={level.id}>
                                    L{level.level_number} - {level.name}
                                  </option>
                                ))}
                              </select>
                            ) : (
                              <div className="flex-1 flex items-center gap-2">
                                <input
                                  type="number"
                                  step={cat.measurement_type === 'TIME' ? '0.01' : '1'}
                                  min="0"
                                  value={entry?.numeric_value ?? ''}
                                  onChange={e => updateLocalProgress(cat.id, {
                                    numeric_value: e.target.value ? Number(e.target.value) : null,
                                  })}
                                  placeholder="--"
                                  className={`w-28 px-3 py-1.5 text-sm border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                                    entry?.numeric_value != null ? 'border-blue-400 bg-blue-50' : 'border-gray-300'
                                  }`}
                                />
                                {cat.measurement_unit && (
                                  <span className="text-xs text-gray-500">{cat.measurement_unit}</span>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ))}

                {/* Save button */}
                <div className="sticky bottom-0 p-5 bg-white border-t border-gray-200">
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 transition text-sm"
                  >
                    {saving ? 'Saving...' : `Save Week ${weekNumber}`}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-6 right-6 bg-gray-900 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-pulse">
          {toast}
        </div>
      )}
    </div>
  );
}
