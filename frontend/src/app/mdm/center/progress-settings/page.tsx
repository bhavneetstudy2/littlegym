'use client';

import { useState, useEffect, useCallback } from 'react';
import { useCenter } from '@/contexts/CenterContext';
import { api } from '@/lib/api';
import { Plus, Trash2, ChevronDown, ChevronRight, ToggleLeft, ToggleRight, Edit2, Check, X } from 'lucide-react';

// ── Types ──────────────────────────────────────────────────────────────────

interface Curriculum { id: number; name: string; description?: string; level?: string; age_min?: number; age_max?: number; is_global: boolean; active: boolean; }
interface ProgressionLevel { id: number; level_number: number; name: string; description?: string; }
interface ActivityCategory { id: number; name: string; category_group?: string; measurement_type: string; measurement_unit?: string; display_order: number; active: boolean | null; progression_levels: ProgressionLevel[]; }
interface Batch { id: number; name: string; }
interface BatchMapping { id: number; batch_id: number; curriculum_id: number; batch_name: string; curriculum_name: string; }

const MEASUREMENT_TYPES = [
  { value: 'LEVEL', label: 'Level (dropdown progression)' },
  { value: 'COUNT', label: 'Count (number of reps)' },
  { value: 'TIME', label: 'Time (duration in seconds)' },
  { value: 'MEASUREMENT', label: 'Measurement (distance/height)' },
];

// ── Main Component ──────────────────────────────────────────────────────────

export default function ProgressSettingsPage() {
  const { selectedCenter } = useCenter();
  const [tab, setTab] = useState<'curricula' | 'activities' | 'mappings'>('curricula');

  // Curricula
  const [curricula, setCurricula] = useState<Curriculum[]>([]);
  const [loadingCurricula, setLoadingCurricula] = useState(false);
  const [showAddCurriculum, setShowAddCurriculum] = useState(false);
  const [editingCurriculumId, setEditingCurriculumId] = useState<number | null>(null);
  const [curriculumForm, setCurriculumForm] = useState({ name: '', description: '', level: '', age_min: '', age_max: '' });

  // Activities
  const [selectedCurriculumId, setSelectedCurriculumId] = useState<number | null>(null);
  const [activities, setActivities] = useState<ActivityCategory[]>([]);
  const [loadingActivities, setLoadingActivities] = useState(false);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [showAddActivity, setShowAddActivity] = useState(false);
  const [activityForm, setActivityForm] = useState({ name: '', category_group: '', measurement_type: 'LEVEL', measurement_unit: '' });
  const [editingActivityId, setEditingActivityId] = useState<number | null>(null);
  const [editActivityForm, setEditActivityForm] = useState({ name: '', category_group: '', measurement_unit: '' });
  // Levels
  const [expandedLevels, setExpandedLevels] = useState<Set<number>>(new Set());
  const [addingLevelFor, setAddingLevelFor] = useState<number | null>(null);
  const [levelForm, setLevelForm] = useState({ level_number: '', name: '', description: '' });

  // Batch mappings
  const [batches, setBatches] = useState<Batch[]>([]);
  const [mappings, setMappings] = useState<BatchMapping[]>([]);
  const [loadingMappings, setLoadingMappings] = useState(false);

  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(null), 3000); };
  const cParam = selectedCenter ? `center_id=${selectedCenter.id}` : '';

  // ── Load curricula ──
  const loadCurricula = useCallback(async () => {
    if (!selectedCenter) return;
    setLoadingCurricula(true);
    try {
      const data = await api.get<Curriculum[]>(`/api/v1/progress/curricula?${cParam}`);
      setCurricula(data);
    } catch { /* ignore */ } finally { setLoadingCurricula(false); }
  }, [selectedCenter, cParam]);

  useEffect(() => { loadCurricula(); }, [loadCurricula]);

  // ── Load activities when curriculum selected ──
  const loadActivities = useCallback(async (currId: number) => {
    setLoadingActivities(true);
    try {
      const data = await api.get<ActivityCategory[]>(
        `/api/v1/progress/activity-categories?curriculum_id=${currId}&include_inactive=true`
      );
      setActivities(data);
      // auto-expand all groups
      const groups = new Set(data.map(a => a.category_group || 'General'));
      setExpandedGroups(groups);
    } catch { setActivities([]); } finally { setLoadingActivities(false); }
  }, []);

  useEffect(() => {
    if (selectedCurriculumId) loadActivities(selectedCurriculumId);
    else setActivities([]);
  }, [selectedCurriculumId, loadActivities]);

  // ── Load batches + mappings ──
  const loadMappings = useCallback(async () => {
    if (!selectedCenter) return;
    setLoadingMappings(true);
    try {
      const [batchData, mappingData] = await Promise.all([
        api.get<Batch[]>(`/api/v1/enrollments/batches?center_id=${selectedCenter.id}&active_only=true`),
        api.get<BatchMapping[]>(`/api/v1/progress/batch-mappings?${cParam}`),
      ]);
      setBatches(batchData);
      setMappings(mappingData);
    } catch { } finally { setLoadingMappings(false); }
  }, [selectedCenter, cParam]);

  useEffect(() => { if (tab === 'mappings') loadMappings(); }, [tab, loadMappings]);

  // ── Curriculum CRUD ──
  const saveCurriculum = async () => {
    if (!curriculumForm.name.trim()) return;
    setSaving(true);
    try {
      const payload = {
        name: curriculumForm.name.trim(),
        description: curriculumForm.description.trim() || null,
        level: curriculumForm.level.trim() || null,
        age_min: curriculumForm.age_min ? Number(curriculumForm.age_min) : null,
        age_max: curriculumForm.age_max ? Number(curriculumForm.age_max) : null,
      };
      if (editingCurriculumId) {
        await api.patch(`/api/v1/progress/curricula/${editingCurriculumId}?${cParam}`, payload);
        showToast('Curriculum updated');
      } else {
        await api.post(`/api/v1/progress/curricula?${cParam}`, payload);
        showToast('Curriculum created');
      }
      setCurriculumForm({ name: '', description: '', level: '', age_min: '', age_max: '' });
      setShowAddCurriculum(false);
      setEditingCurriculumId(null);
      loadCurricula();
    } catch (e: any) { showToast(e.message || 'Failed to save'); } finally { setSaving(false); }
  };

  const toggleCurriculumActive = async (c: Curriculum) => {
    if (c.is_global) return;
    await api.patch(`/api/v1/progress/curricula/${c.id}?${cParam}`, { active: !c.active });
    loadCurricula();
  };

  const startEditCurriculum = (c: Curriculum) => {
    setEditingCurriculumId(c.id);
    setCurriculumForm({ name: c.name, description: c.description || '', level: c.level || '', age_min: c.age_min?.toString() || '', age_max: c.age_max?.toString() || '' });
    setShowAddCurriculum(true);
  };

  // ── Activity CRUD ──
  const saveActivity = async () => {
    if (!activityForm.name.trim() || !selectedCurriculumId) return;
    setSaving(true);
    try {
      await api.post(`/api/v1/progress/activity-categories`, {
        curriculum_id: selectedCurriculumId,
        name: activityForm.name.trim(),
        category_group: activityForm.category_group.trim() || null,
        measurement_type: activityForm.measurement_type,
        measurement_unit: activityForm.measurement_unit.trim() || null,
        display_order: activities.length,
      });
      showToast('Activity added');
      setActivityForm({ name: '', category_group: '', measurement_type: 'LEVEL', measurement_unit: '' });
      setShowAddActivity(false);
      loadActivities(selectedCurriculumId);
    } catch (e: any) { showToast(e.message || 'Failed'); } finally { setSaving(false); }
  };

  const toggleActivityActive = async (a: ActivityCategory) => {
    await api.patch(`/api/v1/progress/activity-categories/${a.id}`, { active: a.active === false ? true : false });
    if (selectedCurriculumId) loadActivities(selectedCurriculumId);
  };

  const deleteActivity = async (id: number) => {
    if (!confirm('Delete this activity? All progress data for it will also be deleted.')) return;
    await api.delete(`/api/v1/progress/activity-categories/${id}`);
    showToast('Activity deleted');
    if (selectedCurriculumId) loadActivities(selectedCurriculumId);
  };

  const saveEditActivity = async (id: number) => {
    await api.patch(`/api/v1/progress/activity-categories/${id}`, {
      name: editActivityForm.name,
      category_group: editActivityForm.category_group || null,
      measurement_unit: editActivityForm.measurement_unit || null,
    });
    setEditingActivityId(null);
    if (selectedCurriculumId) loadActivities(selectedCurriculumId);
  };

  // ── Level CRUD ──
  const saveLevel = async (activityId: number) => {
    if (!levelForm.name.trim() || !levelForm.level_number) return;
    setSaving(true);
    try {
      await api.post(`/api/v1/progress/progression-levels`, {
        activity_category_id: activityId,
        level_number: Number(levelForm.level_number),
        name: levelForm.name.trim(),
        description: levelForm.description.trim() || null,
      });
      setLevelForm({ level_number: '', name: '', description: '' });
      setAddingLevelFor(null);
      if (selectedCurriculumId) loadActivities(selectedCurriculumId);
    } catch (e: any) { showToast(e.message || 'Failed'); } finally { setSaving(false); }
  };

  const deleteLevel = async (levelId: number, actId: number) => {
    await api.delete(`/api/v1/progress/levels/${levelId}`);
    if (selectedCurriculumId) loadActivities(selectedCurriculumId);
  };

  // ── Batch mapping ──
  const assignCurriculum = async (batchId: number, curriculumId: number | null) => {
    if (!curriculumId) {
      // remove mapping
      const m = mappings.find(m => m.batch_id === batchId);
      if (m) {
        await api.delete(`/api/v1/progress/batch-mappings/${m.id}`);
        loadMappings();
      }
    } else {
      await api.post(`/api/v1/progress/batch-mappings?${cParam}`, { batch_id: batchId, curriculum_id: curriculumId });
      loadMappings();
    }
  };

  // ── Grouped activities ──
  const groupedActivities = activities.reduce<Record<string, ActivityCategory[]>>((acc, a) => {
    const g = a.category_group || 'General';
    if (!acc[g]) acc[g] = [];
    acc[g].push(a);
    return acc;
  }, {});

  if (!selectedCenter) {
    return (
      <div className="p-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-yellow-800">
          Please select a center to manage progress settings.
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Progress Tracker Settings</h1>
          <p className="text-gray-500 text-sm mt-1">
            Define curricula, activity fields, and which batch uses which curriculum
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-gray-100 p-1 rounded-lg mb-6 w-fit">
          {(['curricula', 'activities', 'mappings'] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition ${tab === t ? 'bg-white shadow text-blue-700' : 'text-gray-600 hover:text-gray-900'}`}
            >
              {t === 'curricula' ? 'Curricula' : t === 'activities' ? 'Activity Fields' : 'Batch Mapping'}
            </button>
          ))}
        </div>

        {/* ── Tab: Curricula ── */}
        {tab === 'curricula' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-700">Curricula for {selectedCenter.name}</h2>
              <button
                onClick={() => { setShowAddCurriculum(true); setEditingCurriculumId(null); setCurriculumForm({ name: '', description: '', level: '', age_min: '', age_max: '' }); }}
                className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
              >
                <Plus className="w-4 h-4" /> New Curriculum
              </button>
            </div>

            {/* Add/Edit form */}
            {showAddCurriculum && (
              <div className="bg-white border border-blue-200 rounded-xl p-5 mb-4 shadow-sm">
                <h3 className="font-semibold text-gray-800 mb-4">{editingCurriculumId ? 'Edit Curriculum' : 'New Curriculum'}</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-xs font-medium text-gray-600 mb-1">Name *</label>
                    <input
                      value={curriculumForm.name}
                      onChange={e => setCurriculumForm(p => ({ ...p, name: e.target.value }))}
                      placeholder="e.g. Gymnastics Level 1"
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
                    <textarea
                      value={curriculumForm.description}
                      onChange={e => setCurriculumForm(p => ({ ...p, description: e.target.value }))}
                      rows={2}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 resize-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Level label</label>
                    <input value={curriculumForm.level} onChange={e => setCurriculumForm(p => ({ ...p, level: e.target.value }))} placeholder="e.g. Level 1, Beginner" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div className="flex gap-3">
                    <div className="flex-1">
                      <label className="block text-xs font-medium text-gray-600 mb-1">Min Age</label>
                      <input type="number" value={curriculumForm.age_min} onChange={e => setCurriculumForm(p => ({ ...p, age_min: e.target.value }))} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
                    </div>
                    <div className="flex-1">
                      <label className="block text-xs font-medium text-gray-600 mb-1">Max Age</label>
                      <input type="number" value={curriculumForm.age_max} onChange={e => setCurriculumForm(p => ({ ...p, age_max: e.target.value }))} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
                    </div>
                  </div>
                </div>
                <div className="flex justify-end gap-2 mt-4">
                  <button onClick={() => { setShowAddCurriculum(false); setEditingCurriculumId(null); }} className="px-3 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
                  <button onClick={saveCurriculum} disabled={saving || !curriculumForm.name.trim()} className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50">
                    {saving ? 'Saving...' : editingCurriculumId ? 'Update' : 'Create'}
                  </button>
                </div>
              </div>
            )}

            {/* Curriculum list */}
            {loadingCurricula ? (
              <div className="text-gray-400 text-sm py-8 text-center">Loading...</div>
            ) : curricula.length === 0 ? (
              <div className="bg-white rounded-xl border border-dashed border-gray-300 p-10 text-center text-gray-400">
                No curricula yet. Click "New Curriculum" to create one.
              </div>
            ) : (
              <div className="space-y-2">
                {curricula.map(c => (
                  <div key={c.id} className={`bg-white rounded-xl border px-5 py-4 flex items-center justify-between ${c.active ? 'border-gray-200' : 'border-gray-100 opacity-60'}`}>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-gray-900">{c.name}</span>
                        {c.is_global && <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full">Global</span>}
                        {!c.active && <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full">Inactive</span>}
                      </div>
                      {(c.description || c.level || c.age_min || c.age_max) && (
                        <p className="text-xs text-gray-500 mt-0.5">
                          {[c.level, c.age_min && c.age_max ? `Ages ${c.age_min}–${c.age_max}` : null, c.description].filter(Boolean).join(' · ')}
                        </p>
                      )}
                    </div>
                    {!c.is_global && (
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => { setSelectedCurriculumId(c.id); setTab('activities'); }}
                          className="text-xs px-3 py-1.5 border border-blue-200 text-blue-600 rounded-lg hover:bg-blue-50"
                        >
                          Manage Activities
                        </button>
                        <button onClick={() => startEditCurriculum(c)} className="p-1.5 text-gray-400 hover:text-gray-600">
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button onClick={() => toggleCurriculumActive(c)} className="p-1.5 text-gray-400 hover:text-gray-600" title={c.active ? 'Deactivate' : 'Activate'}>
                          {c.active ? <ToggleRight className="w-5 h-5 text-green-500" /> : <ToggleLeft className="w-5 h-5" />}
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── Tab: Activities ── */}
        {tab === 'activities' && (
          <div>
            {/* Curriculum selector */}
            <div className="flex items-center gap-3 mb-5">
              <label className="text-sm font-medium text-gray-600">Curriculum:</label>
              <select
                value={selectedCurriculumId || ''}
                onChange={e => setSelectedCurriculumId(e.target.value ? Number(e.target.value) : null)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Select curriculum --</option>
                {curricula.map(c => (
                  <option key={c.id} value={c.id}>{c.name}{c.is_global ? ' (Global)' : ''}</option>
                ))}
              </select>
              {selectedCurriculumId && (
                <button
                  onClick={() => setShowAddActivity(true)}
                  className="ml-auto flex items-center gap-2 px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
                >
                  <Plus className="w-4 h-4" /> Add Activity
                </button>
              )}
            </div>

            {!selectedCurriculumId ? (
              <div className="bg-white rounded-xl border border-dashed border-gray-300 p-10 text-center text-gray-400">
                Select a curriculum above to manage its activity fields.
              </div>
            ) : (
              <>
                {/* Add activity form */}
                {showAddActivity && (
                  <div className="bg-white border border-blue-200 rounded-xl p-5 mb-4 shadow-sm">
                    <h3 className="font-semibold text-gray-800 mb-4">New Activity Field</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Activity Name *</label>
                        <input value={activityForm.name} onChange={e => setActivityForm(p => ({ ...p, name: e.target.value }))} placeholder="e.g. Cartwheel, Forward Roll" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Group / Category</label>
                        <input value={activityForm.category_group} onChange={e => setActivityForm(p => ({ ...p, category_group: e.target.value }))} placeholder="e.g. Floor Skills, Strength" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Measurement Type</label>
                        <select value={activityForm.measurement_type} onChange={e => setActivityForm(p => ({ ...p, measurement_type: e.target.value }))} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
                          {MEASUREMENT_TYPES.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
                        </select>
                      </div>
                      {activityForm.measurement_type !== 'LEVEL' && (
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Unit (optional)</label>
                          <input value={activityForm.measurement_unit} onChange={e => setActivityForm(p => ({ ...p, measurement_unit: e.target.value }))} placeholder="e.g. reps, seconds, cm" className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
                        </div>
                      )}
                    </div>
                    <div className="flex justify-end gap-2 mt-4">
                      <button onClick={() => setShowAddActivity(false)} className="px-3 py-2 text-sm text-gray-600">Cancel</button>
                      <button onClick={saveActivity} disabled={saving || !activityForm.name.trim()} className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50">
                        {saving ? 'Saving...' : 'Add Activity'}
                      </button>
                    </div>
                  </div>
                )}

                {/* Activity list grouped */}
                {loadingActivities ? (
                  <div className="text-center text-gray-400 py-8">Loading activities...</div>
                ) : activities.length === 0 ? (
                  <div className="bg-white rounded-xl border border-dashed border-gray-300 p-10 text-center text-gray-400">
                    No activities yet. Click "Add Activity" to create the first one.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {Object.entries(groupedActivities).map(([group, cats]) => (
                      <div key={group} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                        {/* Group header */}
                        <button
                          onClick={() => setExpandedGroups(prev => { const n = new Set(prev); n.has(group) ? n.delete(group) : n.add(group); return n; })}
                          className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 text-left"
                        >
                          <span className="font-semibold text-sm text-gray-700 uppercase tracking-wide">{group}</span>
                          <div className="flex items-center gap-2 text-gray-400">
                            <span className="text-xs font-normal normal-case">{cats.length} field{cats.length !== 1 ? 's' : ''}</span>
                            {expandedGroups.has(group) ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                          </div>
                        </button>

                        {expandedGroups.has(group) && (
                          <div className="divide-y divide-gray-100">
                            {cats.map(a => {
                              const isActive = a.active !== false;
                              const isEditing = editingActivityId === a.id;
                              const levelsExpanded = expandedLevels.has(a.id);

                              return (
                                <div key={a.id} className={`${isActive ? '' : 'opacity-50'}`}>
                                  <div className="px-4 py-3 flex items-center gap-3">
                                    {/* Activity name / edit */}
                                    <div className="flex-1 min-w-0">
                                      {isEditing ? (
                                        <div className="flex items-center gap-2">
                                          <input
                                            value={editActivityForm.name}
                                            onChange={e => setEditActivityForm(p => ({ ...p, name: e.target.value }))}
                                            className="border border-blue-300 rounded px-2 py-1 text-sm flex-1"
                                          />
                                          <input
                                            value={editActivityForm.category_group}
                                            onChange={e => setEditActivityForm(p => ({ ...p, category_group: e.target.value }))}
                                            placeholder="Group"
                                            className="border border-gray-300 rounded px-2 py-1 text-sm w-28"
                                          />
                                        </div>
                                      ) : (
                                        <span className="text-sm font-medium text-gray-900">{a.name}</span>
                                      )}
                                      {!isEditing && (
                                        <span className="ml-2 text-xs text-gray-400">
                                          {MEASUREMENT_TYPES.find(m => m.value === a.measurement_type)?.label.split(' ')[0]}
                                          {a.measurement_unit ? ` (${a.measurement_unit})` : ''}
                                        </span>
                                      )}
                                    </div>

                                    {/* Level count for LEVEL type */}
                                    {a.measurement_type === 'LEVEL' && !isEditing && (
                                      <button
                                        onClick={() => setExpandedLevels(prev => { const n = new Set(prev); n.has(a.id) ? n.delete(a.id) : n.add(a.id); return n; })}
                                        className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
                                      >
                                        {a.progression_levels.length} level{a.progression_levels.length !== 1 ? 's' : ''}
                                        {levelsExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                                      </button>
                                    )}

                                    {/* Action buttons */}
                                    {isEditing ? (
                                      <>
                                        <button onClick={() => saveEditActivity(a.id)} className="p-1 text-green-600 hover:text-green-700"><Check className="w-4 h-4" /></button>
                                        <button onClick={() => setEditingActivityId(null)} className="p-1 text-gray-400 hover:text-gray-600"><X className="w-4 h-4" /></button>
                                      </>
                                    ) : (
                                      <>
                                        <button onClick={() => { setEditingActivityId(a.id); setEditActivityForm({ name: a.name, category_group: a.category_group || '', measurement_unit: a.measurement_unit || '' }); }} className="p-1.5 text-gray-400 hover:text-gray-600">
                                          <Edit2 className="w-4 h-4" />
                                        </button>
                                        <button onClick={() => toggleActivityActive(a)} className="p-1.5" title={isActive ? 'Disable' : 'Enable'}>
                                          {isActive ? <ToggleRight className="w-5 h-5 text-green-500" /> : <ToggleLeft className="w-5 h-5 text-gray-400" />}
                                        </button>
                                        <button onClick={() => deleteActivity(a.id)} className="p-1.5 text-gray-400 hover:text-red-500">
                                          <Trash2 className="w-4 h-4" />
                                        </button>
                                      </>
                                    )}
                                  </div>

                                  {/* Levels (for LEVEL type) */}
                                  {a.measurement_type === 'LEVEL' && levelsExpanded && (
                                    <div className="bg-gray-50 px-6 pb-3">
                                      <div className="space-y-1 mb-2">
                                        {a.progression_levels.length === 0 && (
                                          <p className="text-xs text-gray-400 py-1">No levels yet</p>
                                        )}
                                        {a.progression_levels.map(lv => (
                                          <div key={lv.id} className="flex items-center gap-2 text-sm py-1">
                                            <span className="text-xs font-bold text-blue-600 w-6">L{lv.level_number}</span>
                                            <span className="text-gray-800">{lv.name}</span>
                                            {lv.description && <span className="text-gray-400 text-xs">· {lv.description}</span>}
                                            <button onClick={() => deleteLevel(lv.id, a.id)} className="ml-auto p-1 text-gray-300 hover:text-red-500">
                                              <Trash2 className="w-3 h-3" />
                                            </button>
                                          </div>
                                        ))}
                                      </div>

                                      {/* Add level */}
                                      {addingLevelFor === a.id ? (
                                        <div className="flex items-center gap-2">
                                          <input type="number" min="1" placeholder="L#" value={levelForm.level_number} onChange={e => setLevelForm(p => ({ ...p, level_number: e.target.value }))} className="w-14 border border-gray-300 rounded px-2 py-1 text-xs" />
                                          <input placeholder="Level name" value={levelForm.name} onChange={e => setLevelForm(p => ({ ...p, name: e.target.value }))} className="flex-1 border border-gray-300 rounded px-2 py-1 text-xs" />
                                          <input placeholder="Description (opt)" value={levelForm.description} onChange={e => setLevelForm(p => ({ ...p, description: e.target.value }))} className="flex-1 border border-gray-300 rounded px-2 py-1 text-xs" />
                                          <button onClick={() => saveLevel(a.id)} disabled={saving} className="px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50">Add</button>
                                          <button onClick={() => setAddingLevelFor(null)} className="p-1 text-gray-400"><X className="w-3 h-3" /></button>
                                        </div>
                                      ) : (
                                        <button onClick={() => { setAddingLevelFor(a.id); setLevelForm({ level_number: String(a.progression_levels.length + 1), name: '', description: '' }); }} className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1">
                                          <Plus className="w-3 h-3" /> Add Level
                                        </button>
                                      )}
                                    </div>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* ── Tab: Batch Mapping ── */}
        {tab === 'mappings' && (
          <div>
            <p className="text-sm text-gray-500 mb-4">
              Assign a curriculum to each batch. The Progress Tracker will use this mapping to load the correct activity fields.
            </p>
            {loadingMappings ? (
              <div className="text-center text-gray-400 py-8">Loading...</div>
            ) : batches.length === 0 ? (
              <div className="bg-white rounded-xl border border-dashed border-gray-300 p-10 text-center text-gray-400">
                No batches found. Create batches in Master Data → Batches first.
              </div>
            ) : (
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div className="grid grid-cols-2 px-5 py-3 bg-gray-50 border-b border-gray-200 text-xs font-semibold text-gray-600 uppercase tracking-wide">
                  <span>Batch</span>
                  <span>Curriculum</span>
                </div>
                <div className="divide-y divide-gray-100">
                  {batches.map(batch => {
                    const existing = mappings.find(m => m.batch_id === batch.id);
                    return (
                      <div key={batch.id} className="grid grid-cols-2 items-center px-5 py-3">
                        <span className="font-medium text-gray-900 text-sm">{batch.name}</span>
                        <select
                          value={existing?.curriculum_id || ''}
                          onChange={e => assignCurriculum(batch.id, e.target.value ? Number(e.target.value) : null)}
                          className={`border rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 ${existing ? 'border-green-300 bg-green-50 text-green-800' : 'border-gray-300 text-gray-500'}`}
                        >
                          <option value="">— Not mapped —</option>
                          {curricula.map(c => (
                            <option key={c.id} value={c.id}>{c.name}{c.is_global ? ' (Global)' : ''}</option>
                          ))}
                        </select>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-6 right-6 bg-gray-900 text-white px-6 py-3 rounded-lg shadow-lg z-50">
          {toast}
        </div>
      )}
    </div>
  );
}
