'use client';

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useCenter } from '@/contexts/CenterContext';
import type {
  Batch, ActivityCategory,
  WeeklyProgressResponse, WeeklyProgressBulkPayload, WeeklyProgressEntry,
  BatchStudentProgressSummary, ChildTrainerNotes,
} from '@/types';

interface BatchMapping { id: number; batch_id: number; curriculum_id: number; curriculum_name: string; }
interface Curriculum { id: number; name: string; }

// ── helpers ──────────────────────────────────────────────────────────────────

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  return name.slice(0, 2).toUpperCase();
}

function getAvatarColor(name: string): string {
  const colors = ['bg-violet-500', 'bg-emerald-500', 'bg-blue-500', 'bg-amber-500',
    'bg-rose-500', 'bg-cyan-500', 'bg-indigo-500', 'bg-teal-500', 'bg-orange-500', 'bg-pink-500'];
  let h = 0;
  for (let i = 0; i < name.length; i++) h = name.charCodeAt(i) + ((h << 5) - h);
  return colors[Math.abs(h) % colors.length];
}

function weekDateRange(startDate: string | null, weekNumber: number): string {
  if (!startDate) return '';
  const base = new Date(startDate);
  const offset = (weekNumber - 1) * 7;
  const ws = new Date(base.getTime() + offset * 86400000);
  const we = new Date(ws.getTime() + 6 * 86400000);
  const fmt = (d: Date) => d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
  return `${fmt(ws)} – ${fmt(we)}`;
}

function weekStartDate(startDate: string | null, weekNumber: number): string {
  if (!startDate) return new Date().toISOString().split('T')[0];
  const base = new Date(startDate);
  const d = new Date(base.getTime() + (weekNumber - 1) * 7 * 86400000);
  return d.toISOString().split('T')[0];
}

// Chip level style helper
function chipStyle(isSelected: boolean, levelNumber: number): string {
  if (!isSelected) return 'border border-gray-200 bg-white text-gray-500';
  if (levelNumber === 1) return 'border border-gray-400 bg-gray-100 text-gray-700 font-semibold';
  if (levelNumber === 2) return 'border border-amber-400 bg-amber-50 text-amber-800 font-semibold';
  return 'border border-green-500 bg-green-50 text-green-800 font-semibold';
}

// ── main component ────────────────────────────────────────────────────────────

export default function ProgressPage() {
  const { selectedCenter } = useCenter();
  const router = useRouter();
  const centerParam = selectedCenter ? `center_id=${selectedCenter.id}` : '';

  // Selection state
  const [batches, setBatches] = useState<Batch[]>([]);
  const [selectedBatchId, setSelectedBatchId] = useState<number | null>(null);
  const [batchMappings, setBatchMappings] = useState<BatchMapping[]>([]);
  const [curricula, setCurricula] = useState<Curriculum[]>([]);
  const [selectedCurriculumId, setSelectedCurriculumId] = useState<number | null>(null);
  const [activityCategories, setActivityCategories] = useState<ActivityCategory[]>([]);

  // Students
  const [students, setStudents] = useState<BatchStudentProgressSummary[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loadingStudents, setLoadingStudents] = useState(false);

  // Selected student + week
  const [selectedStudent, setSelectedStudent] = useState<BatchStudentProgressSummary | null>(null);
  const [weekNumber, setWeekNumber] = useState(1);
  const [weekProgress, setWeekProgress] = useState<Record<number, WeeklyProgressEntry>>({});
  const [parentExpectation, setParentExpectation] = useState('');
  const [progressCheck, setProgressCheck] = useState('');

  // Saving states
  const [savingSkill, setSavingSkill] = useState<number | null>(null);   // activity_category_id being saved
  const [savingNotes, setSavingNotes] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(false);
  const [loadingBatches, setLoadingBatches] = useState(true);
  const [toast, setToast] = useState<string | null>(null);

  // Mobile: track if skill sheet is open (full-screen overlay)
  const [sheetOpen, setSheetOpen] = useState(false);
  // Collapsible notes section (collapsed by default for more skill space)
  const [notesOpen, setNotesOpen] = useState(false);
  // Collapsible skill groups
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({});

  const notesDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(null), 2500); };

  // ── Load batches + mappings + curricula ───────────────────────────────────

  useEffect(() => {
    if (!selectedCenter) return;
    const load = async () => {
      setLoadingBatches(true);
      try {
        const batchData = await api.get<Batch[]>(`/api/v1/enrollments/batches?${centerParam}`);
        const activeBatches = batchData.filter(b => b.active);
        setBatches(activeBatches);

        const [mappingData, currData] = await Promise.all([
          api.get<BatchMapping[]>(`/api/v1/progress/batch-mappings?${centerParam}`).catch(() => [] as BatchMapping[]),
          api.get<Curriculum[]>(`/api/v1/progress/curricula?${centerParam}`).catch(() => [] as Curriculum[]),
        ]);
        setBatchMappings(mappingData);
        setCurricula(currData);

        if (activeBatches.length > 0 && !selectedBatchId) {
          // Prefer a batch that has a curriculum mapped, otherwise first batch
          const batchWithCurriculum = activeBatches.find(b => mappingData.some(m => m.batch_id === b.id));
          const firstBatch = batchWithCurriculum || activeBatches[0];
          setSelectedBatchId(firstBatch.id);
          const mapping = mappingData.find(m => m.batch_id === firstBatch.id);
          if (mapping) setSelectedCurriculumId(mapping.curriculum_id);
        }
      } catch (err) {
        console.error('Failed to load batches:', err);
      } finally {
        setLoadingBatches(false);
      }
    };
    load();
  }, [selectedCenter]);

  // When batch changes, auto-select its curriculum
  useEffect(() => {
    if (!selectedBatchId) return;
    const mapping = batchMappings.find(m => m.batch_id === selectedBatchId);
    setSelectedCurriculumId(mapping ? mapping.curriculum_id : null);
    setSelectedStudent(null);
    setSheetOpen(false);
  }, [selectedBatchId, batchMappings]);

  // Load activity categories when curriculum changes
  useEffect(() => {
    if (!selectedCurriculumId) { setActivityCategories([]); return; }
    api.get<ActivityCategory[]>(`/api/v1/progress/activity-categories?curriculum_id=${selectedCurriculumId}`)
      .then(d => setActivityCategories(d))
      .catch(() => setActivityCategories([]));
  }, [selectedCurriculumId]);

  // Load students when batch/curriculum changes
  useEffect(() => {
    if (!selectedBatchId || !selectedCurriculumId || !selectedCenter) return;
    setLoadingStudents(true);
    api.get<BatchStudentProgressSummary[]>(
      `/api/v1/progress/batch-summary/${selectedBatchId}?curriculum_id=${selectedCurriculumId}&${centerParam}`
    ).then(d => setStudents(d)).catch(() => setStudents([])).finally(() => setLoadingStudents(false));
  }, [selectedBatchId, selectedCurriculumId, selectedCenter]);

  // Load weekly progress for a student+week
  const loadProgress = useCallback(async (student: BatchStudentProgressSummary, week: number) => {
    setLoadingProgress(true);
    try {
      const [progressData, notesData] = await Promise.all([
        api.get<WeeklyProgressResponse[]>(
          `/api/v1/progress/weekly/${student.child_id}?week_number=${week}&enrollment_id=${student.enrollment_id || ''}&${centerParam}`
        ),
        api.get<ChildTrainerNotes | null>(
          `/api/v1/progress/trainer-notes/${student.child_id}?enrollment_id=${student.enrollment_id || ''}&${centerParam}`
        ).catch(() => null),
      ]);
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
      setParentExpectation(notesData?.parent_expectation || '');
      setProgressCheck(notesData?.progress_check || '');
    } catch (err) {
      console.error('Failed to load progress:', err);
    } finally {
      setLoadingProgress(false);
    }
  }, [centerParam]);

  const openStudent = (student: BatchStudentProgressSummary) => {
    setSelectedStudent(student);
    setWeekNumber(student.current_week);
    loadProgress(student, student.current_week);
    setSheetOpen(true);
  };

  const changeWeek = (delta: number) => {
    if (!selectedStudent) return;
    const nw = Math.max(1, weekNumber + delta);
    setWeekNumber(nw);
    loadProgress(selectedStudent, nw);
  };

  // ── Auto-save: tap a chip → immediately save that skill ───────────────────

  const saveSkill = async (student: BatchStudentProgressSummary, actCatId: number, levelId: number | null) => {
    setSavingSkill(actCatId);
    // Update local state first for instant feedback
    setWeekProgress(prev => ({
      ...prev,
      [actCatId]: {
        activity_category_id: actCatId,
        progression_level_id: levelId,
        numeric_value: prev[actCatId]?.numeric_value ?? null,
        notes: prev[actCatId]?.notes ?? null,
      },
    }));
    try {
      // Build full entries list (all current skill values)
      const entries: WeeklyProgressEntry[] = activityCategories.map(cat => {
        if (cat.id === actCatId) {
          return { activity_category_id: actCatId, progression_level_id: levelId, numeric_value: null, notes: null };
        }
        const cur = weekProgress[cat.id];
        return {
          activity_category_id: cat.id,
          progression_level_id: cur?.progression_level_id ?? null,
          numeric_value: cur?.numeric_value ?? null,
          notes: cur?.notes ?? null,
        };
      });
      const payload: WeeklyProgressBulkPayload = {
        child_id: student.child_id,
        enrollment_id: student.enrollment_id,
        week_number: weekNumber,
        week_start_date: weekStartDate(student.enrollment_start_date, weekNumber),
        entries,
      };
      await api.post(`/api/v1/progress/weekly/bulk-update?${centerParam}`, payload);
    } catch {
      showToast('Failed to save — check connection');
    } finally {
      setSavingSkill(null);
    }
  };

  // ── Debounced notes save ───────────────────────────────────────────────────

  const saveNotes = useCallback(async (student: BatchStudentProgressSummary, expectation: string, check: string) => {
    setSavingNotes(true);
    try {
      await api.post(`/api/v1/progress/trainer-notes?${centerParam}`, {
        child_id: student.child_id,
        enrollment_id: student.enrollment_id,
        parent_expectation: expectation,
        progress_check: check,
      });
    } catch {
      // silent
    } finally {
      setSavingNotes(false);
    }
  }, [centerParam]);

  const onNotesChange = (field: 'expectation' | 'check', value: string) => {
    if (field === 'expectation') setParentExpectation(value);
    else setProgressCheck(value);
    if (notesDebounceRef.current) clearTimeout(notesDebounceRef.current);
    notesDebounceRef.current = setTimeout(() => {
      if (!selectedStudent) return;
      const exp = field === 'expectation' ? value : parentExpectation;
      const chk = field === 'check' ? value : progressCheck;
      saveNotes(selectedStudent, exp, chk);
    }, 800);
  };

  // ── Grouped activities ─────────────────────────────────────────────────────

  const groupedActivities = useMemo(() => {
    const groups: Record<string, ActivityCategory[]> = {};
    for (const cat of activityCategories) {
      const g = cat.category_group || 'General';
      if (!groups[g]) groups[g] = [];
      groups[g].push(cat);
    }
    return groups;
  }, [activityCategories]);

  const filteredStudents = useMemo(() => {
    if (!searchQuery) return students;
    const q = searchQuery.toLowerCase();
    return students.filter(s => s.child_name.toLowerCase().includes(q));
  }, [students, searchQuery]);

  const currentMapping = selectedBatchId ? batchMappings.find(m => m.batch_id === selectedBatchId) : null;

  // ── Loading ────────────────────────────────────────────────────────────────

  if (loadingBatches) {
    return (
      <div className="p-4 md:p-6">
        <h1 className="text-xl font-bold text-gray-900 mb-4">Progress Tracker</h1>
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="bg-white rounded-xl p-4 animate-pulse border border-gray-100">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-200 rounded-full" />
                <div className="flex-1"><div className="h-4 bg-gray-200 rounded w-32 mb-1" /><div className="h-3 bg-gray-200 rounded w-20" /></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!selectedCenter) {
    return (
      <div className="p-4 md:p-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 text-yellow-800 text-sm">
          Please select a center to view progress tracking.
        </div>
      </div>
    );
  }

  if (batches.length === 0) {
    return (
      <div className="p-4 md:p-6">
        <h1 className="text-xl font-bold text-gray-900 mb-4">Progress Tracker</h1>
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 text-yellow-900">
          <p className="font-semibold text-sm mb-1">No batches found</p>
          <p className="text-xs">Create batches in Master Data → Batches first.</p>
        </div>
      </div>
    );
  }

  // ── Skill Sheet (full-screen on mobile) ────────────────────────────────────

  const SkillSheet = () => {
    if (!selectedStudent) return null;
    return (
      <div className={`
        fixed inset-0 z-40 bg-white flex flex-col
        lg:relative lg:inset-auto lg:z-auto lg:flex lg:flex-col lg:rounded-xl lg:border lg:border-gray-200 lg:shadow-sm lg:overflow-hidden
        ${sheetOpen ? 'flex' : 'hidden lg:flex'}
      `}>
        {/* Header */}
        <div className="flex items-center gap-3 px-4 py-3 bg-white border-b border-gray-200 shrink-0">
          {/* Back button — mobile only */}
          <button
            onClick={() => { setSheetOpen(false); setSelectedStudent(null); }}
            className="lg:hidden p-2 -ml-2 text-gray-500 hover:text-gray-700 active:bg-gray-100 rounded-lg"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold ${getAvatarColor(selectedStudent.child_name)}`}>
                {getInitials(selectedStudent.child_name)}
              </div>
              <div className="min-w-0">
                <h2 className="font-bold text-gray-900 text-base leading-tight truncate">{selectedStudent.child_name}</h2>
                <p className="text-xs text-gray-500 leading-tight">{weekDateRange(selectedStudent.enrollment_start_date, weekNumber)}</p>
              </div>
            </div>
          </div>
          {/* Week nav */}
          <div className="flex items-center gap-1 shrink-0">
            <button
              onClick={() => changeWeek(-1)}
              disabled={weekNumber <= 1 || loadingProgress}
              className="w-8 h-8 flex items-center justify-center text-gray-500 hover:text-gray-700 disabled:opacity-30 active:bg-gray-100 rounded-lg"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <span className="text-sm font-bold text-blue-600 w-12 text-center">Wk {weekNumber}</span>
            <button
              onClick={() => changeWeek(1)}
              disabled={loadingProgress}
              className="w-8 h-8 flex items-center justify-center text-gray-500 hover:text-gray-700 disabled:opacity-30 active:bg-gray-100 rounded-lg"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
          {/* Close — desktop */}
          <button
            onClick={() => { setSheetOpen(false); setSelectedStudent(null); }}
            className="hidden lg:flex w-8 h-8 items-center justify-center text-gray-400 hover:text-gray-600 rounded-lg"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        {loadingProgress ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              <p className="text-sm text-gray-500">Loading...</p>
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto overscroll-contain">

            {/* ── Collapsible Notes Section ── */}
            <div className="border-b border-gray-100">
              <button
                onClick={() => setNotesOpen(o => !o)}
                className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  <span className="text-sm font-semibold text-gray-700">Trainer Notes</span>
                  {savingNotes && <span className="text-xs text-blue-500">saving...</span>}
                  {(parentExpectation || progressCheck) && (
                    <span className="w-2 h-2 bg-blue-400 rounded-full" />
                  )}
                </div>
                <svg className={`w-4 h-4 text-gray-400 transition-transform ${notesOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {notesOpen && (
                <div className="px-4 pb-4 grid grid-cols-1 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wide">Parent Expectation</label>
                    <textarea
                      value={parentExpectation}
                      onChange={e => onNotesChange('expectation', e.target.value)}
                      rows={2}
                      placeholder="What does the parent want to work on?"
                      className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 resize-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wide">Progress Check</label>
                    <textarea
                      value={progressCheck}
                      onChange={e => onNotesChange('check', e.target.value)}
                      rows={2}
                      placeholder="Trainer's observations this week"
                      className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 resize-none"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* ── Skill groups ── */}
            {activityCategories.length === 0 ? (
              <div className="p-8 text-center text-gray-400 text-sm">
                No activity fields defined for this curriculum.
                <br />
                <button onClick={() => router.push('/mdm/center/progress-settings')} className="text-blue-600 hover:underline mt-2 block mx-auto">
                  Set up in Master Data →
                </button>
              </div>
            ) : (
              Object.entries(groupedActivities).map(([groupName, cats]) => {
                const isGroupCollapsed = collapsedGroups[groupName] ?? false;
                return (
                  <div key={groupName} className="border-b border-gray-100 last:border-0">
                    {/* Collapsible group header */}
                    <button
                      onClick={() => setCollapsedGroups(prev => ({ ...prev, [groupName]: !prev[groupName] }))}
                      className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors sticky top-0 z-10"
                    >
                      <h3 className="text-xs font-bold text-gray-600 uppercase tracking-wider">{groupName}</h3>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-400">{cats.length} skills</span>
                        <svg className={`w-3.5 h-3.5 text-gray-400 transition-transform ${isGroupCollapsed ? '-rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                    </button>

                    {/* Skills */}
                    {!isGroupCollapsed && cats.map(cat => {
                      const entry = weekProgress[cat.id];
                      const isSaving = savingSkill === cat.id;
                      const isLevel = cat.measurement_type === 'LEVEL';
                      const hasValue = entry?.progression_level_id != null || entry?.numeric_value != null;

                      return (
                        <div key={cat.id} className={`px-4 py-4 border-b border-gray-50 last:border-0 ${hasValue ? 'bg-white' : 'bg-white'}`}>
                          {/* Skill name row */}
                          <div className="flex items-center justify-between mb-3">
                            <span className="text-sm font-semibold text-gray-800">{cat.name}</span>
                            {isSaving && (
                              <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin shrink-0" />
                            )}
                          </div>

                          {/* Chips — LEVEL type (full width, equal size) */}
                          {isLevel ? (
                            <div className="grid grid-cols-3 gap-2">
                              {cat.progression_levels.map(level => {
                                const isSelected = entry?.progression_level_id === level.id;
                                return (
                                  <button
                                    key={level.id}
                                    onClick={() => saveSkill(selectedStudent, cat.id, isSelected ? null : level.id)}
                                    disabled={isSaving}
                                    className={`
                                      py-2.5 px-2 rounded-xl text-sm font-medium transition-all active:scale-95
                                      text-center min-h-[44px] disabled:opacity-60
                                      ${chipStyle(isSelected, level.level_number)}
                                    `}
                                  >
                                    {level.name}
                                  </button>
                                );
                              })}
                            </div>
                          ) : (
                            /* Numeric type */
                            <div className="flex items-center gap-2">
                              <input
                                type="number"
                                step={cat.measurement_type === 'TIME' ? '0.1' : '1'}
                                min="0"
                                value={entry?.numeric_value ?? ''}
                                onChange={e => {
                                  const val = e.target.value ? Number(e.target.value) : null;
                                  setWeekProgress(prev => ({
                                    ...prev,
                                    [cat.id]: { ...prev[cat.id], activity_category_id: cat.id, numeric_value: val, progression_level_id: null, notes: null },
                                  }));
                                }}
                                onBlur={e => {
                                  const val = e.target.value ? Number(e.target.value) : null;
                                  saveSkill(selectedStudent, cat.id, null);
                                  void api.post(`/api/v1/progress/weekly/bulk-update?${centerParam}`, {
                                    child_id: selectedStudent.child_id,
                                    enrollment_id: selectedStudent.enrollment_id,
                                    week_number: weekNumber,
                                    week_start_date: weekStartDate(selectedStudent.enrollment_start_date, weekNumber),
                                    entries: activityCategories.map(c => ({
                                      activity_category_id: c.id,
                                      progression_level_id: c.id === cat.id ? null : (weekProgress[c.id]?.progression_level_id ?? null),
                                      numeric_value: c.id === cat.id ? val : (weekProgress[c.id]?.numeric_value ?? null),
                                      notes: weekProgress[c.id]?.notes ?? null,
                                    })),
                                  } as WeeklyProgressBulkPayload).catch(() => {});
                                }}
                                placeholder="—"
                                className="w-28 px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 text-center"
                              />
                              {cat.measurement_unit && <span className="text-xs text-gray-500">{cat.measurement_unit}</span>}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                );
              })
            )}

            {/* Bottom safe area */}
            <div className="h-8" />
          </div>
        )}
      </div>
    );
  };

  // ── Main render ────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col h-full min-h-screen bg-gray-50">
      {/* Top bar */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between mb-3">
          <h1 className="text-lg font-bold text-gray-900">Progress Tracker</h1>
          {currentMapping ? (
            <span className="text-xs bg-blue-50 border border-blue-200 text-blue-700 px-2.5 py-1 rounded-full">
              {currentMapping.curriculum_name}
            </span>
          ) : selectedBatchId ? (
            <button
              onClick={() => router.push('/mdm/center/progress-settings?tab=mappings')}
              className="text-xs bg-orange-50 border border-orange-200 text-orange-700 px-2.5 py-1 rounded-full"
            >
              No curriculum mapped
            </button>
          ) : null}
        </div>

        {/* Batch tabs — horizontal scroll */}
        <div className="flex gap-2 overflow-x-auto pb-0.5 -mx-1 px-1 scrollbar-none">
          {batches.map(batch => {
            const hasCurriculum = batchMappings.some(m => m.batch_id === batch.id);
            return (
              <button
                key={batch.id}
                onClick={() => { setSelectedBatchId(batch.id); setSelectedStudent(null); setSheetOpen(false); }}
                className={`
                  px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition shrink-0
                  ${selectedBatchId === batch.id
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'bg-white text-gray-700 border border-gray-300'}
                `}
              >
                {batch.name}
                {!hasCurriculum && <span className="ml-1 opacity-60 text-xs">⚠</span>}
              </button>
            );
          })}
        </div>
      </div>

      {/* No curriculum mapped */}
      {selectedBatchId && !selectedCurriculumId && (
        <div className="m-4 bg-orange-50 border border-orange-200 rounded-xl p-4">
          <p className="font-semibold text-orange-900 text-sm mb-1">No curriculum mapped to this batch</p>
          <p className="text-xs text-orange-800 mb-3">
            Go to Master Data → Progress Settings to create a curriculum and map this batch.
          </p>
          <button
            onClick={() => router.push('/mdm/center/progress-settings')}
            className="px-4 py-2 bg-orange-600 text-white text-sm rounded-lg"
          >
            Set up Progress Settings →
          </button>
        </div>
      )}

      {selectedBatchId && selectedCurriculumId && (
        <div className="flex flex-col lg:flex-row flex-1 overflow-hidden">
          {/* Student list */}
          <div className={`
            flex flex-col lg:w-80 lg:border-r lg:border-gray-200 bg-white
            ${sheetOpen ? 'hidden lg:flex' : 'flex'}
          `}>
            {/* Search */}
            <div className="p-3 border-b border-gray-100">
              <div className="relative">
                <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  type="text"
                  placeholder="Search student..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 text-sm border border-gray-200 rounded-xl bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:bg-white"
                />
              </div>
            </div>

            {/* Student cards */}
            <div className="flex-1 overflow-y-auto overscroll-contain">
              {loadingStudents ? (
                <div className="space-y-1 p-3">
                  {[1, 2, 3, 4].map(i => (
                    <div key={i} className="flex items-center gap-3 p-3 rounded-xl animate-pulse">
                      <div className="w-10 h-10 bg-gray-200 rounded-full shrink-0" />
                      <div className="flex-1"><div className="h-4 bg-gray-200 rounded w-28 mb-1" /><div className="h-3 bg-gray-200 rounded w-20" /></div>
                    </div>
                  ))}
                </div>
              ) : filteredStudents.length === 0 ? (
                <div className="p-8 text-center text-gray-400 text-sm">
                  {students.length === 0 ? 'No enrolled students in this batch' : 'No students found'}
                </div>
              ) : (
                <div className="p-2 space-y-1">
                  {filteredStudents.map(student => {
                    const isSelected = selectedStudent?.child_id === student.child_id;
                    const pct = student.total_activities > 0
                      ? Math.round((student.completed_activities / student.total_activities) * 100) : 0;
                    return (
                      <button
                        key={student.child_id}
                        onClick={() => openStudent(student)}
                        className={`
                          w-full text-left p-3 rounded-xl transition active:scale-[0.98]
                          ${isSelected ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-50 border border-transparent'}
                        `}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-bold shrink-0 ${getAvatarColor(student.child_name)}`}>
                            {getInitials(student.child_name)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="font-semibold text-gray-900 text-sm truncate">{student.child_name}</div>
                            <div className="flex items-center gap-2 mt-1">
                              <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                  className={`h-full rounded-full ${pct >= 80 ? 'bg-green-500' : pct >= 40 ? 'bg-blue-500' : pct > 0 ? 'bg-amber-500' : 'bg-gray-300'}`}
                                  style={{ width: `${pct}%` }}
                                />
                              </div>
                              <span className="text-xs text-gray-400 shrink-0">Wk {student.current_week}</span>
                            </div>
                          </div>
                          <svg className="w-4 h-4 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Skill sheet — desktop side panel or mobile full screen */}
          <div className="flex-1 overflow-hidden">
            {selectedStudent ? (
              <SkillSheet />
            ) : (
              <div className="hidden lg:flex h-full items-center justify-center text-gray-400">
                <div className="text-center">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <svg className="w-8 h-8 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                  <p className="text-sm">Select a student to view progress</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-gray-900 text-white px-5 py-2.5 rounded-full shadow-lg z-50 text-sm whitespace-nowrap">
          {toast}
        </div>
      )}
    </div>
  );
}
