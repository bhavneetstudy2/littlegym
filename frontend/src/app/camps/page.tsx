'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { useCenter } from '@/contexts/CenterContext';
import { Calendar, Plus, Users, X, ChevronRight, Tent } from 'lucide-react';

interface Camp {
  id: number;
  center_id: number;
  name: string;
  description: string | null;
  start_date: string;
  end_date: string;
  capacity: number | null;
  price: number | null;
  active: boolean;
  status: 'UPCOMING' | 'ACTIVE' | 'COMPLETED';
  enrolled_count: number;
}

interface CampEnrollment {
  id: number;
  camp_id: number;
  is_existing_student: boolean;
  child_id: number | null;
  child_name: string | null;
  child_dob: string | null;
  parent_name: string | null;
  parent_phone: string | null;
  parent_email: string | null;
  notes: string | null;
  status: string;
  payment_status: string;
  payment_amount: number | null;
  amount_paid: number | null;
  payment_method: string | null;
  payment_reference: string | null;
  payment_date: string | null;
  lead_created?: boolean;
  created_at: string | null;
}

interface StudentOption {
  child_id: number;
  child_name: string;
  enrollment_id: number;
  batch_name: string | null;
}

const STATUS_BADGE: Record<string, string> = {
  UPCOMING: 'bg-blue-100 text-blue-700',
  ACTIVE: 'bg-green-100 text-green-700',
  COMPLETED: 'bg-gray-100 text-gray-600',
};

function fmtDate(d: string) {
  return new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

// ── Create Camp Modal ──────────────────────────────────────────────────────

function CreateCampModal({ onClose, onCreated, centerParam }: {
  onClose: () => void;
  onCreated: (c: Camp) => void;
  centerParam: string;
}) {
  const [form, setForm] = useState({
    name: '',
    description: '',
    start_date: '',
    end_date: '',
    capacity: '',
    price: '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const submit = async () => {
    if (!form.name || !form.start_date || !form.end_date) {
      setError('Name, start date and end date are required.');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const camp = await api.post<Camp>(`/api/v1/camps?${centerParam}`, {
        name: form.name,
        description: form.description || null,
        start_date: form.start_date,
        end_date: form.end_date,
        capacity: form.capacity ? Number(form.capacity) : null,
        price: form.price ? Number(form.price) : null,
      });
      onCreated(camp);
    } catch (e: unknown) {
      const err = e as { message?: string };
      setError(err?.message || 'Failed to create camp');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-md shadow-xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 className="text-base font-bold text-gray-900">Create Camp</h2>
          <button onClick={onClose} className="p-1.5 text-gray-400 hover:text-gray-700 rounded-lg"><X className="w-4 h-4" /></button>
        </div>
        <div className="p-5 space-y-4">
          {error && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>}
          <div>
            <label className="block text-xs font-semibold text-gray-500 mb-1">Camp Name *</label>
            <input
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="e.g. Spring Camp 2026"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-500 mb-1">Description</label>
            <textarea
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 resize-none"
              rows={2}
              placeholder="Optional details about the camp"
              value={form.description}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-gray-500 mb-1">Start Date *</label>
              <input type="date" className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                value={form.start_date} onChange={e => setForm(f => ({ ...f, start_date: e.target.value }))} />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 mb-1">End Date *</label>
              <input type="date" className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                value={form.end_date} onChange={e => setForm(f => ({ ...f, end_date: e.target.value }))} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-gray-500 mb-1">Capacity</label>
              <input type="number" min="1" className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Optional"
                value={form.capacity} onChange={e => setForm(f => ({ ...f, capacity: e.target.value }))} />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 mb-1">Price (₹)</label>
              <input type="number" min="0" className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Optional"
                value={form.price} onChange={e => setForm(f => ({ ...f, price: e.target.value }))} />
            </div>
          </div>
        </div>
        <div className="px-5 pb-5 flex gap-3">
          <button onClick={onClose} className="flex-1 px-4 py-2.5 text-sm border border-gray-200 rounded-xl text-gray-700 hover:bg-gray-50">Cancel</button>
          <button onClick={submit} disabled={saving} className="flex-1 px-4 py-2.5 text-sm bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-60">
            {saving ? 'Creating...' : 'Create Camp'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Enroll Modal ────────────────────────────────────────────────────────────

function EnrollModal({ camp, onClose, onEnrolled, centerParam, centerId }: {
  camp: Camp;
  onClose: () => void;
  onEnrolled: (e: CampEnrollment) => void;
  centerParam: string;
  centerId: number | null;
}) {
  const [isExisting, setIsExisting] = useState(true);
  const [studentSearch, setStudentSearch] = useState('');
  const [studentOptions, setStudentOptions] = useState<StudentOption[]>([]);
  const [selectedStudent, setSelectedStudent] = useState<StudentOption | null>(null);
  const [searching, setSearching] = useState(false);

  const [form, setForm] = useState({
    child_name: '',
    child_dob: '',
    parent_name: '',
    parent_phone: '',
    parent_email: '',
    notes: '',
    payment_status: 'PENDING',
    payment_amount: '',
    amount_paid: '',
    payment_method: '',
    payment_reference: '',
    payment_date: '',
  });

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  // Search existing students
  useEffect(() => {
    if (!isExisting || studentSearch.length < 2 || !centerId) {
      setStudentOptions([]);
      return;
    }
    setSearching(true);
    api.get<StudentOption[]>(
      `/api/v1/camps/children-search?center_id=${centerId}&search=${encodeURIComponent(studentSearch)}&limit=20`
    ).then(setStudentOptions).catch(() => setStudentOptions([])).finally(() => setSearching(false));
  }, [isExisting, studentSearch, centerId]);

  const submit = async () => {
    setError('');
    if (isExisting && !selectedStudent) { setError('Please select a student.'); return; }
    if (!isExisting && !form.child_name) { setError('Child name is required.'); return; }

    setSaving(true);
    try {
      const paymentFields = {
        payment_status: form.payment_status || 'PENDING',
        payment_amount: form.payment_amount ? Number(form.payment_amount) : null,
        amount_paid: form.amount_paid ? Number(form.amount_paid) : null,
        payment_method: form.payment_method || null,
        payment_reference: form.payment_reference || null,
        payment_date: form.payment_date || null,
      };
      const payload = isExisting
        ? { is_existing_student: true, child_id: selectedStudent!.child_id, notes: form.notes || null, ...paymentFields }
        : {
            is_existing_student: false,
            child_name: form.child_name,
            child_dob: form.child_dob || null,
            parent_name: form.parent_name || null,
            parent_phone: form.parent_phone || null,
            parent_email: form.parent_email || null,
            notes: form.notes || null,
            ...paymentFields,
          };

      const enrollment = await api.post<CampEnrollment>(
        `/api/v1/camps/${camp.id}/enrollments?${centerParam}`,
        payload
      );
      onEnrolled(enrollment);
    } catch (e: unknown) {
      const err = e as { message?: string };
      setError(err?.message || 'Failed to enroll student');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-md shadow-xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 shrink-0">
          <div>
            <h2 className="text-base font-bold text-gray-900">Enroll Student</h2>
            <p className="text-xs text-gray-500 mt-0.5">{camp.name}</p>
          </div>
          <button onClick={onClose} className="p-1.5 text-gray-400 hover:text-gray-700 rounded-lg"><X className="w-4 h-4" /></button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {error && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>}

          {/* Toggle */}
          <div className="flex gap-2">
            <button
              onClick={() => { setIsExisting(true); setSelectedStudent(null); setStudentSearch(''); }}
              className={`flex-1 py-2.5 text-sm font-medium rounded-xl border transition ${isExisting ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-200 text-gray-600 hover:bg-gray-50'}`}
            >
              Existing Student
            </button>
            <button
              onClick={() => setIsExisting(false)}
              className={`flex-1 py-2.5 text-sm font-medium rounded-xl border transition ${!isExisting ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-200 text-gray-600 hover:bg-gray-50'}`}
            >
              New Student
            </button>
          </div>

          {isExisting ? (
            <>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Search Student *</label>
                <input
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Type name to search..."
                  value={studentSearch}
                  onChange={e => { setStudentSearch(e.target.value); setSelectedStudent(null); }}
                />
                {searching && <p className="text-xs text-gray-400 mt-1">Searching...</p>}
                {studentOptions.length > 0 && !selectedStudent && (
                  <div className="mt-1 border border-gray-200 rounded-xl overflow-hidden shadow-sm max-h-40 overflow-y-auto">
                    {studentOptions.map(s => (
                      <button
                        key={s.child_id}
                        onClick={() => { setSelectedStudent(s); setStudentSearch(s.child_name); setStudentOptions([]); }}
                        className="w-full text-left px-3 py-2.5 text-sm hover:bg-blue-50 border-b border-gray-100 last:border-0"
                      >
                        <span className="font-medium text-gray-900">{s.child_name}</span>
                        {s.batch_name && <span className="ml-2 text-xs text-gray-400">{s.batch_name}</span>}
                      </button>
                    ))}
                  </div>
                )}
                {selectedStudent && (
                  <div className="mt-2 flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2">
                    <span className="text-sm font-medium text-blue-800">{selectedStudent.child_name}</span>
                    <button onClick={() => { setSelectedStudent(null); setStudentSearch(''); }} className="ml-auto text-blue-400 hover:text-blue-700"><X className="w-3.5 h-3.5" /></button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Child Name *</label>
                <input className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Child's full name"
                  value={form.child_name} onChange={e => setForm(f => ({ ...f, child_name: e.target.value }))} />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Date of Birth</label>
                <input type="date" className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                  value={form.child_dob} onChange={e => setForm(f => ({ ...f, child_dob: e.target.value }))} />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Parent Name</label>
                <input className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Parent / guardian name"
                  value={form.parent_name} onChange={e => setForm(f => ({ ...f, parent_name: e.target.value }))} />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Parent Phone</label>
                <input className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="+91 XXXXX XXXXX"
                  value={form.parent_phone} onChange={e => setForm(f => ({ ...f, parent_phone: e.target.value }))} />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Parent Email</label>
                <input type="email" className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="email@example.com"
                  value={form.parent_email} onChange={e => setForm(f => ({ ...f, parent_email: e.target.value }))} />
              </div>
            </>
          )}

          {/* Payment section */}
          <div className="border-t border-gray-100 pt-4">
            <p className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-3">Payment</p>
            <div className="space-y-3">
              <div className="grid grid-cols-3 gap-2">
                {(['PENDING', 'PARTIAL', 'PAID'] as const).map(s => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setForm(f => ({ ...f, payment_status: s }))}
                    className={`py-2 rounded-xl text-xs font-semibold border transition ${
                      form.payment_status === s
                        ? s === 'PAID' ? 'bg-green-500 text-white border-green-500'
                          : s === 'PARTIAL' ? 'bg-amber-500 text-white border-amber-500'
                          : 'bg-gray-500 text-white border-gray-500'
                        : 'bg-white text-gray-500 border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-500 mb-1">Total Fee (₹)</label>
                  <input type="number" min="0" className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="0"
                    value={form.payment_amount} onChange={e => setForm(f => ({ ...f, payment_amount: e.target.value }))} />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-500 mb-1">Amount Paid (₹)</label>
                  <input type="number" min="0" className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="0"
                    value={form.amount_paid} onChange={e => setForm(f => ({ ...f, amount_paid: e.target.value }))} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-500 mb-1">Method</label>
                  <select className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white"
                    value={form.payment_method} onChange={e => setForm(f => ({ ...f, payment_method: e.target.value }))}>
                    <option value="">Select...</option>
                    <option>CASH</option>
                    <option>UPI</option>
                    <option>CARD</option>
                    <option>BANK_TRANSFER</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-500 mb-1">Date</label>
                  <input type="date" className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                    value={form.payment_date} onChange={e => setForm(f => ({ ...f, payment_date: e.target.value }))} />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Reference / Transaction ID</label>
                <input className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="UPI ref, cheque no, etc."
                  value={form.payment_reference} onChange={e => setForm(f => ({ ...f, payment_reference: e.target.value }))} />
              </div>
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-500 mb-1">Notes</label>
            <textarea className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 resize-none"
              rows={2} placeholder="Any special notes..."
              value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} />
          </div>
        </div>

        <div className="px-5 pb-5 flex gap-3 shrink-0 border-t border-gray-100 pt-4">
          <button onClick={onClose} className="flex-1 px-4 py-2.5 text-sm border border-gray-200 rounded-xl text-gray-700 hover:bg-gray-50">Cancel</button>
          <button onClick={submit} disabled={saving} className="flex-1 px-4 py-2.5 text-sm bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-60">
            {saving ? 'Enrolling...' : 'Enroll'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main page ────────────────────────────────────────────────────────────────

export default function CampsPage() {
  const { selectedCenter } = useCenter();
  const centerParam = selectedCenter ? `center_id=${selectedCenter.id}` : '';
  const [userRole, setUserRole] = useState<string>('');
  useEffect(() => {
    try {
      const u = JSON.parse(localStorage.getItem('user') || '{}');
      setUserRole(u.role || '');
    } catch { /* ignore */ }
  }, []);
  const canManageCamps = userRole === 'SUPER_ADMIN' || userRole === 'CENTER_ADMIN';

  const [camps, setCamps] = useState<Camp[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const [selectedCamp, setSelectedCamp] = useState<Camp | null>(null);
  const [enrollments, setEnrollments] = useState<CampEnrollment[]>([]);
  const [loadingEnrollments, setLoadingEnrollments] = useState(false);
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [cancellingId, setCancellingId] = useState<number | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(null), 4000); };

  const loadCamps = useCallback(async () => {
    if (!selectedCenter) return;
    setLoading(true);
    try {
      const data = await api.get<Camp[]>(`/api/v1/camps?${centerParam}`);
      setCamps(data);
    } catch {
      setCamps([]);
    } finally {
      setLoading(false);
    }
  }, [selectedCenter, centerParam]);

  useEffect(() => { loadCamps(); }, [loadCamps]);

  const loadEnrollments = useCallback(async (campId: number) => {
    setLoadingEnrollments(true);
    try {
      const data = await api.get<CampEnrollment[]>(`/api/v1/camps/${campId}/enrollments`);
      setEnrollments(data.filter(e => e.status === 'ENROLLED'));
    } catch {
      setEnrollments([]);
    } finally {
      setLoadingEnrollments(false);
    }
  }, []);

  const openCamp = (camp: Camp) => {
    setSelectedCamp(camp);
    loadEnrollments(camp.id);
  };

  const cancelEnrollment = async (enrollment: CampEnrollment) => {
    if (!selectedCamp) return;
    setCancellingId(enrollment.id);
    try {
      await api.patch(`/api/v1/camps/${selectedCamp.id}/enrollments/${enrollment.id}/cancel`, {});
      setEnrollments(prev => prev.filter(e => e.id !== enrollment.id));
      setCamps(prev => prev.map(c => c.id === selectedCamp.id ? { ...c, enrolled_count: c.enrolled_count - 1 } : c));
    } catch {
      // silently ignore
    } finally {
      setCancellingId(null);
    }
  };

  if (!selectedCenter) {
    return (
      <div className="p-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 text-yellow-800 text-sm">
          Please select a center to view camps.
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-orange-100 rounded-xl flex items-center justify-center">
            <Tent className="w-5 h-5 text-orange-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Camps</h1>
            <p className="text-sm text-gray-500">Short-term camp programs</p>
          </div>
        </div>
        {canManageCamps && (
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-xl hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
            Create Camp
          </button>
        )}
      </div>

      <div className="flex flex-col lg:flex-row gap-4">
        {/* Camp list */}
        <div className="flex-1">
          {loading ? (
            <div className="space-y-3">
              {[1, 2].map(i => (
                <div key={i} className="bg-white rounded-xl border border-gray-100 p-4 animate-pulse">
                  <div className="h-5 bg-gray-200 rounded w-40 mb-2" />
                  <div className="h-3 bg-gray-200 rounded w-56" />
                </div>
              ))}
            </div>
          ) : camps.length === 0 ? (
            <div className="bg-white border border-gray-100 rounded-xl p-10 text-center">
              <Tent className="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 text-sm font-medium mb-1">No camps yet</p>
              <p className="text-gray-400 text-xs">Create a camp to get started.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {camps.map(camp => {
                const isSelected = selectedCamp?.id === camp.id;
                const weeks = Math.round(
                  (new Date(camp.end_date).getTime() - new Date(camp.start_date).getTime()) / (7 * 86400000)
                );
                return (
                  <button
                    key={camp.id}
                    onClick={() => openCamp(camp)}
                    className={`w-full text-left bg-white border rounded-xl p-4 transition hover:shadow-sm ${isSelected ? 'border-blue-400 ring-1 ring-blue-300' : 'border-gray-100 hover:border-gray-200'}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-semibold text-gray-900 text-base">{camp.name}</span>
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_BADGE[camp.status]}`}>
                            {camp.status}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-500">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3.5 h-3.5" />
                            {fmtDate(camp.start_date)} – {fmtDate(camp.end_date)}
                          </span>
                          <span>{weeks} week{weeks !== 1 ? 's' : ''}</span>
                          {camp.price !== null && <span>₹{camp.price}</span>}
                        </div>
                        {camp.description && (
                          <p className="text-xs text-gray-400 mt-1.5 truncate">{camp.description}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-3 shrink-0 ml-3">
                        <div className="text-right">
                          <div className="flex items-center gap-1 text-sm font-bold text-gray-700">
                            <Users className="w-3.5 h-3.5 text-gray-400" />
                            {camp.enrolled_count}
                            {camp.capacity && <span className="text-gray-400 font-normal text-xs">/{camp.capacity}</span>}
                          </div>
                          <p className="text-xs text-gray-400">enrolled</p>
                        </div>
                        <ChevronRight className="w-4 h-4 text-gray-400" />
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Enrollment panel */}
        {selectedCamp && (
          <div className="lg:w-96 bg-white border border-gray-100 rounded-xl flex flex-col max-h-[600px]">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 shrink-0">
              <div>
                <h2 className="font-bold text-gray-900 text-sm">{selectedCamp.name}</h2>
                <p className="text-xs text-gray-400 mt-0.5">{selectedCamp.enrolled_count} enrolled</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowEnrollModal(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded-lg hover:bg-blue-700"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Enroll
                </button>
                <button onClick={() => { setSelectedCamp(null); setEnrollments([]); }} className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg">
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto">
              {loadingEnrollments ? (
                <div className="p-6 space-y-2">
                  {[1, 2, 3].map(i => <div key={i} className="h-12 bg-gray-100 rounded-xl animate-pulse" />)}
                </div>
              ) : enrollments.length === 0 ? (
                <div className="p-8 text-center text-gray-400 text-sm">
                  <Users className="w-8 h-8 mx-auto mb-2 text-gray-200" />
                  No students enrolled yet.
                  <br />
                  <button onClick={() => setShowEnrollModal(true)} className="text-blue-600 hover:underline mt-1 text-xs">Enroll first student →</button>
                </div>
              ) : (
                <div className="divide-y divide-gray-50">
                  {enrollments.map(e => (
                    <div key={e.id} className="flex items-center gap-3 px-4 py-3">
                      <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center shrink-0">
                        {(e.child_name || '?').charAt(0).toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          <p className="text-sm font-medium text-gray-900 truncate">{e.child_name || '—'}</p>
                          {e.is_existing_student ? (
                            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-green-100 text-green-700 font-medium shrink-0">Existing</span>
                          ) : (
                            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-orange-100 text-orange-700 font-medium shrink-0">New</span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 mt-0.5 text-xs text-gray-400">
                          {/* Payment status badge */}
                          <span className={`font-semibold ${
                            e.payment_status === 'PAID' ? 'text-green-600'
                            : e.payment_status === 'PARTIAL' ? 'text-amber-600'
                            : 'text-gray-400'
                          }`}>
                            {e.payment_status === 'PAID' ? '✓ Paid'
                              : e.payment_status === 'PARTIAL' ? `Partial ₹${e.amount_paid ?? 0}`
                              : 'Pending'}
                          </span>
                          {e.payment_amount && <span className="text-gray-300">· ₹{e.payment_amount} total</span>}
                          {e.payment_method && <span>{e.payment_method}</span>}
                        </div>
                        {e.parent_phone && <p className="text-xs text-gray-400 mt-0.5">{e.parent_phone}</p>}
                      </div>
                      <button
                        onClick={() => cancelEnrollment(e)}
                        disabled={cancellingId === e.id}
                        className="p-1.5 text-gray-300 hover:text-red-500 rounded-lg transition disabled:opacity-40"
                        title="Cancel enrollment"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      {showCreateModal && (
        <CreateCampModal
          centerParam={centerParam}
          onClose={() => setShowCreateModal(false)}
          onCreated={camp => {
            setCamps(prev => [camp, ...prev]);
            setShowCreateModal(false);
          }}
        />
      )}

      {showEnrollModal && selectedCamp && (
        <EnrollModal
          camp={selectedCamp}
          centerParam={centerParam}
          centerId={selectedCenter?.id ?? null}
          onClose={() => setShowEnrollModal(false)}
          onEnrolled={enrollment => {
            setEnrollments(prev => [...prev, enrollment]);
            setCamps(prev => prev.map(c => c.id === selectedCamp.id ? { ...c, enrolled_count: c.enrolled_count + 1 } : c));
            setShowEnrollModal(false);
            if (enrollment.lead_created) {
              showToast(`${enrollment.child_name} enrolled + added to Leads as enquiry`);
            } else {
              showToast(`${enrollment.child_name} enrolled in ${selectedCamp.name}`);
            }
          }}
        />
      )}

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-gray-900 text-white px-5 py-3 rounded-full shadow-lg z-50 text-sm whitespace-nowrap flex items-center gap-2">
          <span>{toast}</span>
        </div>
      )}
    </div>
  );
}
