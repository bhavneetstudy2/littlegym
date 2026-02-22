'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import DateInput from '@/components/ui/DateInput';

interface Child {
  id: number;
  enquiry_id?: string;
  first_name: string;
  last_name?: string;
  dob?: string;
  age_years?: number;
  school?: string;
  interests?: string[];
  notes?: string;
}

interface Parent {
  id: number;
  name: string;
  phone: string;
  email?: string;
  relationship_type?: string;
  is_primary_contact: boolean;
}

interface BatchInfo {
  id: number;
  name: string;
  age_min?: number;
  age_max?: number;
  days_of_week?: string[];
  start_time?: string;
  end_time?: string;
}

interface EnrolledStudent {
  enrollment_id: number;
  plan_type: string;
  status: string;
  start_date?: string;
  end_date?: string;
  visits_included?: number;
  visits_used: number;
  days_selected?: string[];
  enrollment_notes?: string;
  enrolled_at: string;
  child: Child;
  parents: Parent[];
  batch?: BatchInfo;
  total_paid: number;
  total_discount: number;
  payment_method?: string;
}

interface AttendanceRecord {
  id: number;
  class_session_id: number;
  child_id: number;
  status: string;
  marked_at?: string;
  session_date?: string;
  batch_id?: number;
  batch_name?: string;
  notes?: string;
  created_at: string;
}

interface SkillProgress {
  id: number;
  skill_id: number;
  skill_name: string;
  category?: string;
  level: string;
  last_updated_at?: string;
  notes?: string;
}

// Helpers
const formatDate = (dateString?: string) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  });
};

const calculateAge = (dob?: string) => {
  if (!dob) return null;
  const today = new Date();
  const birthDate = new Date(dob);
  let age = today.getFullYear() - birthDate.getFullYear();
  const m = today.getMonth() - birthDate.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }
  return age;
};

const getStatusBadge = (status: string) => {
  const styles: Record<string, string> = {
    'ACTIVE': 'bg-green-100 text-green-800',
    'EXPIRED': 'bg-red-100 text-red-800',
    'PAUSED': 'bg-yellow-100 text-yellow-800',
    'CANCELLED': 'bg-gray-100 text-gray-800',
    'PRESENT': 'bg-green-100 text-green-800',
    'ABSENT': 'bg-red-100 text-red-800',
    'MAKEUP': 'bg-yellow-100 text-yellow-800',
    'TRIAL': 'bg-blue-100 text-blue-800',
  };
  return styles[status] || 'bg-gray-100 text-gray-800';
};

const getSkillLevelBadge = (level: string) => {
  const styles: Record<string, string> = {
    'NOT_STARTED': 'bg-gray-100 text-gray-600',
    'IN_PROGRESS': 'bg-yellow-100 text-yellow-800',
    'ACHIEVED': 'bg-blue-100 text-blue-800',
    'MASTERED': 'bg-green-100 text-green-800',
  };
  return styles[level] || 'bg-gray-100 text-gray-800';
};

const getPlanDisplay = (planType: string) => {
  const types: Record<string, string> = {
    'PAY_PER_VISIT': 'Per Visit',
    'WEEKLY': 'Weekly',
    'MONTHLY': 'Monthly',
    'QUARTERLY': 'Quarterly',
    'SEMI_ANNUALLY': 'Semi-Annual',
    'YEARLY': 'Yearly',
    'CUSTOM': 'Custom'
  };
  return types[planType] || planType;
};

interface StudentProfileContentProps {
  childId: number;
  enrollmentId?: number;
  centerId: number;
  onClose?: () => void;
  onBack?: () => void;
}

export default function StudentProfileContent({ childId, centerId, onClose, onBack }: StudentProfileContentProps) {
  const [allEnrollments, setAllEnrollments] = useState<EnrolledStudent[]>([]);
  const [childInfo, setChildInfo] = useState<Child | null>(null);
  const [parents, setParents] = useState<Parent[]>([]);
  const [attendance, setAttendance] = useState<AttendanceRecord[]>([]);
  const [skillProgress, setSkillProgress] = useState<SkillProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'attendance' | 'progress'>('overview');
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({ first_name: '', last_name: '', dob: '', school: '', notes: '', age_years: '' });
  const [saving, setSaving] = useState(false);
  const [editingParentId, setEditingParentId] = useState<number | null>(null);
  const [parentEditData, setParentEditData] = useState({ name: '', phone: '', email: '' });
  const [savingParent, setSavingParent] = useState(false);
  const [statusChangeId, setStatusChangeId] = useState<number | null>(null);
  const [statusSaving, setStatusSaving] = useState(false);
  const [editingEnrollmentId, setEditingEnrollmentId] = useState<number | null>(null);
  const [enrollmentEditData, setEnrollmentEditData] = useState({ visits_included: '', start_date: '', end_date: '', notes: '' });
  const [savingEnrollment, setSavingEnrollment] = useState(false);
  const [renewEnrollment, setRenewEnrollment] = useState<EnrolledStudent | null>(null);

  useEffect(() => {
    if (childId && centerId) {
      fetchStudentData();
    }
  }, [childId, centerId]);

  const fetchStudentData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch only this child's enrollments (not all students)
      const childEnrollments = await api.get<EnrolledStudent[]>(
        `/api/v1/enrollments/students?center_id=${centerId}&child_id=${childId}&limit=100`
      );

      if (childEnrollments.length > 0) {
        // Sort: ACTIVE first, then by enrolled_at descending
        const statusOrder: Record<string, number> = { 'ACTIVE': 0, 'PAUSED': 1, 'EXPIRED': 2, 'CANCELLED': 3 };
        childEnrollments.sort((a, b) => {
          const orderA = statusOrder[a.status] ?? 99;
          const orderB = statusOrder[b.status] ?? 99;
          if (orderA !== orderB) return orderA - orderB;
          return new Date(b.enrolled_at).getTime() - new Date(a.enrolled_at).getTime();
        });

        setAllEnrollments(childEnrollments);
        setChildInfo(childEnrollments[0].child);
        setParents(childEnrollments[0].parents);
      } else {
        setError('Student not found');
      }

      // Fetch attendance history
      try {
        const attendanceRes = await api.get<AttendanceRecord[]>(
          `/api/v1/attendance/children/${childId}`
        );
        setAttendance(attendanceRes);
      } catch (err) {
        console.error('Failed to load attendance:', err);
      }

      // Fetch skill progress
      try {
        const progressRes = await api.get<SkillProgress[]>(
          `/api/v1/curriculum/progress/children/${childId}`
        );
        setSkillProgress(progressRes);
      } catch (err) {
        console.error('Failed to load skill progress:', err);
      }

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load student data');
    } finally {
      setLoading(false);
    }
  };

  const startEditing = () => {
    if (!childInfo) return;
    setEditData({
      first_name: childInfo.first_name || '',
      last_name: childInfo.last_name || '',
      dob: childInfo.dob || '',
      school: childInfo.school || '',
      notes: childInfo.notes || '',
      age_years: childInfo.age_years ? String(childInfo.age_years) : '',
    });
    setIsEditing(true);
  };

  const saveEdit = async () => {
    if (!childInfo) return;
    setSaving(true);
    try {
      const payload = {
        ...editData,
        age_years: editData.age_years ? parseInt(editData.age_years) : null,
      };
      await api.patch(`/api/v1/enrollments/children/${childInfo.id}?center_id=${centerId}`, payload);
      setChildInfo({ ...childInfo, ...editData, age_years: editData.age_years ? parseInt(editData.age_years) : undefined });
      setIsEditing(false);
    } catch (err: any) {
      alert(err.message || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const startEditingParent = (parent: Parent) => {
    setParentEditData({
      name: parent.name || '',
      phone: parent.phone || '',
      email: parent.email || '',
    });
    setEditingParentId(parent.id);
  };

  const saveParentEdit = async () => {
    if (!editingParentId) return;
    setSavingParent(true);
    try {
      await api.patch(`/api/v1/leads/parent/${editingParentId}`, parentEditData);
      setParents(prev => prev.map(p =>
        p.id === editingParentId ? { ...p, ...parentEditData } : p
      ));
      setEditingParentId(null);
    } catch (err: any) {
      alert(err.message || 'Failed to save parent');
    } finally {
      setSavingParent(false);
    }
  };

  const changeEnrollmentStatus = async (enrollmentId: number, newStatus: string) => {
    setStatusSaving(true);
    setStatusChangeId(enrollmentId);
    try {
      await api.patch(`/api/v1/enrollments/${enrollmentId}`, { status: newStatus });
      setAllEnrollments(prev => prev.map(e =>
        e.enrollment_id === enrollmentId ? { ...e, status: newStatus } : e
      ));
    } catch (err: any) {
      alert(err.message || 'Failed to update status');
    } finally {
      setStatusSaving(false);
      setStatusChangeId(null);
    }
  };

  const startEditingEnrollment = (enrollment: EnrolledStudent) => {
    setEnrollmentEditData({
      visits_included: enrollment.visits_included ? String(enrollment.visits_included) : '',
      start_date: enrollment.start_date || '',
      end_date: enrollment.end_date || '',
      notes: enrollment.enrollment_notes || '',
    });
    setEditingEnrollmentId(enrollment.enrollment_id);
  };

  const saveEnrollmentEdit = async () => {
    if (!editingEnrollmentId) return;
    setSavingEnrollment(true);
    try {
      const payload: Record<string, unknown> = {};
      if (enrollmentEditData.visits_included) payload.visits_included = parseInt(enrollmentEditData.visits_included);
      if (enrollmentEditData.start_date) payload.start_date = enrollmentEditData.start_date;
      if (enrollmentEditData.end_date) payload.end_date = enrollmentEditData.end_date;
      payload.notes = enrollmentEditData.notes || null;

      await api.patch(`/api/v1/enrollments/${editingEnrollmentId}`, payload);
      setAllEnrollments(prev => prev.map(e =>
        e.enrollment_id === editingEnrollmentId ? {
          ...e,
          visits_included: enrollmentEditData.visits_included ? parseInt(enrollmentEditData.visits_included) : e.visits_included,
          start_date: enrollmentEditData.start_date || e.start_date,
          end_date: enrollmentEditData.end_date || e.end_date,
          enrollment_notes: enrollmentEditData.notes || undefined,
        } : e
      ));
      setEditingEnrollmentId(null);
    } catch (err: any) {
      alert(err.message || 'Failed to update enrollment');
    } finally {
      setSavingEnrollment(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading student profile...</p>
      </div>
    );
  }

  if (error || !childInfo || allEnrollments.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <p className="text-red-500 mb-4">{error || 'Student not found'}</p>
        {onClose && (
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Close
          </button>
        )}
        {onBack && (
          <button
            onClick={onBack}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            Back to search
          </button>
        )}
      </div>
    );
  }

  const age = calculateAge(childInfo.dob);
  const primaryParent = parents.find(p => p.is_primary_contact) || parents[0];

  // Group attendance by batch
  const attendanceByBatch: Record<string, AttendanceRecord[]> = {};
  for (const record of attendance) {
    const batchKey = record.batch_name || 'Unknown Batch';
    if (!attendanceByBatch[batchKey]) {
      attendanceByBatch[batchKey] = [];
    }
    attendanceByBatch[batchKey].push(record);
  }

  // Overall attendance stats
  const totalPresent = attendance.filter(a => a.status === 'PRESENT').length;
  const totalAbsent = attendance.filter(a => a.status === 'ABSENT').length;
  const totalSessions = attendance.length;
  const overallRate = totalSessions > 0 ? Math.round((totalPresent / totalSessions) * 100) : 0;

  // Total stats across all enrollments
  const totalBooked = allEnrollments.reduce((sum, e) => sum + (e.visits_included || 0), 0);
  const totalAttended = allEnrollments.reduce((sum, e) => sum + (e.visits_used || 0), 0);
  const totalRemaining = allEnrollments.reduce((sum, e) => sum + Math.max(0, (e.visits_included || 0) - (e.visits_used || 0)), 0);
  const activeEnrollments = allEnrollments.filter(e => e.status === 'ACTIVE');

  return (
    <>
      {/* Header */}
      <div className="bg-white border-b p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {onBack && (
              <button
                onClick={onBack}
                className="text-gray-400 hover:text-gray-600 transition"
                title="Back to search"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
            )}
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                {childInfo.first_name} {childInfo.last_name || ''}
                {childInfo.enquiry_id && (
                  <span className="ml-2 text-sm font-normal text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                    {childInfo.enquiry_id}
                  </span>
                )}
              </h2>
              <p className="text-sm text-gray-500">
                {age ? `${age} years` : childInfo.age_years ? `${childInfo.age_years} years` : ''}
                {primaryParent ? ` | ${primaryParent.name} (${primaryParent.phone})` : ''}
                {` | ${allEnrollments.length} enrollment${allEnrollments.length > 1 ? 's' : ''}`}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {activeEnrollments.length > 0 && (
              <span className="px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                {activeEnrollments.length} Active
              </span>
            )}
            {allEnrollments.filter(e => e.status === 'EXPIRED').length > 0 && (
              <span className="px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                {allEnrollments.filter(e => e.status === 'EXPIRED').length} Expired
              </span>
            )}
            {onClose && (
              <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl ml-2">
                &times;
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b bg-white px-4">
        <nav className="flex gap-4">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'overview'
                ? 'border-green-500 text-green-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('attendance')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'attendance'
                ? 'border-green-500 text-green-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Attendance ({totalSessions})
          </button>
          <button
            onClick={() => setActiveTab('progress')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'progress'
                ? 'border-green-500 text-green-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Progress ({skillProgress.length})
          </button>
        </nav>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6 bg-gray-50">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-white rounded-lg shadow p-4">
                <div className="text-sm text-gray-500">Total Booked</div>
                <div className="text-2xl font-bold text-blue-600">{totalBooked || '-'}</div>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <div className="text-sm text-gray-500">Total Attended</div>
                <div className="text-2xl font-bold text-green-600">{totalAttended}</div>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <div className="text-sm text-gray-500">Remaining (Active)</div>
                <div className="text-2xl font-bold text-orange-600">{totalRemaining || '-'}</div>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <div className="text-sm text-gray-500">Attendance Rate</div>
                <div className="text-2xl font-bold text-purple-600">{overallRate}%</div>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <div className="text-sm text-gray-500">Enrollments</div>
                <div className="text-2xl font-bold text-indigo-600">{allEnrollments.length}</div>
              </div>
            </div>

            {/* Child Information */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4 border-b pb-2">
                <h3 className="text-lg font-semibold text-gray-900">Child Information</h3>
                {!isEditing ? (
                  <button onClick={startEditing} className="text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                    Edit
                  </button>
                ) : (
                  <div className="flex gap-2">
                    <button onClick={() => setIsEditing(false)} className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1 border border-gray-300 rounded">Cancel</button>
                    <button onClick={saveEdit} disabled={saving} className="text-sm text-white bg-green-600 hover:bg-green-700 px-3 py-1 rounded disabled:opacity-50">
                      {saving ? 'Saving...' : 'Save'}
                    </button>
                  </div>
                )}
              </div>
              {isEditing ? (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-gray-500 text-sm block mb-1">First Name</label>
                    <input type="text" value={editData.first_name} onChange={e => setEditData({...editData, first_name: e.target.value})} className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm" />
                  </div>
                  <div>
                    <label className="text-gray-500 text-sm block mb-1">Last Name</label>
                    <input type="text" value={editData.last_name} onChange={e => setEditData({...editData, last_name: e.target.value})} className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm" />
                  </div>
                  <div>
                    <label className="text-gray-500 text-sm block mb-1">Date of Birth</label>
                    <input type="date" value={editData.dob} onChange={e => setEditData({...editData, dob: e.target.value})} className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm" />
                  </div>
                  <div>
                    <label className="text-gray-500 text-sm block mb-1">Age (years)</label>
                    <input type="number" value={editData.age_years} onChange={e => setEditData({...editData, age_years: e.target.value})} min="0" max="25" className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm" placeholder="e.g. 5" />
                  </div>
                  <div>
                    <label className="text-gray-500 text-sm block mb-1">School</label>
                    <input type="text" value={editData.school} onChange={e => setEditData({...editData, school: e.target.value})} className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm" />
                  </div>
                  <div className="col-span-2">
                    <label className="text-gray-500 text-sm block mb-1">Notes</label>
                    <textarea value={editData.notes} onChange={e => setEditData({...editData, notes: e.target.value})} rows={2} className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm" />
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-gray-500 text-sm">Full Name</span>
                    <p className="font-medium">{childInfo.first_name} {childInfo.last_name || ''}</p>
                  </div>
                  <div>
                    <span className="text-gray-500 text-sm">TLG ID / Enquiry ID</span>
                    <p className="font-medium text-blue-600">{childInfo.enquiry_id || '-'}</p>
                  </div>
                  <div>
                    <span className="text-gray-500 text-sm">Date of Birth / Age</span>
                    <p className="font-medium">
                      {childInfo.dob
                        ? `${formatDate(childInfo.dob)} (${age} years)`
                        : childInfo.age_years
                          ? `${childInfo.age_years} years`
                          : '-'}
                    </p>
                  </div>
                  <div>
                    <span className="text-gray-500 text-sm">School</span>
                    <p className="font-medium">{childInfo.school || '-'}</p>
                  </div>
                  <div>
                    <span className="text-gray-500 text-sm">Interests</span>
                    <p className="font-medium">{childInfo.interests?.join(', ') || '-'}</p>
                  </div>
                  {childInfo.notes && (
                    <div className="col-span-2">
                      <span className="text-gray-500 text-sm">Notes</span>
                      <p className="font-medium">{childInfo.notes}</p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Parent Information */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Parent/Guardian Information</h3>
              <div className="space-y-4">
                {parents.map((parent, idx) => (
                  <div key={idx} className="bg-gray-50 p-4 rounded-lg">
                    {editingParentId === parent.id ? (
                      <div>
                        <div className="grid grid-cols-3 gap-3 mb-3">
                          <div>
                            <label className="text-gray-500 text-xs block mb-1">Name</label>
                            <input type="text" value={parentEditData.name} onChange={e => setParentEditData({...parentEditData, name: e.target.value})} className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm" />
                          </div>
                          <div>
                            <label className="text-gray-500 text-xs block mb-1">Phone</label>
                            <input type="text" value={parentEditData.phone} onChange={e => setParentEditData({...parentEditData, phone: e.target.value})} className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm" />
                          </div>
                          <div>
                            <label className="text-gray-500 text-xs block mb-1">Email</label>
                            <input type="text" value={parentEditData.email} onChange={e => setParentEditData({...parentEditData, email: e.target.value})} className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm" />
                          </div>
                        </div>
                        <div className="flex gap-2 justify-end">
                          <button onClick={() => setEditingParentId(null)} className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1 border border-gray-300 rounded">Cancel</button>
                          <button onClick={saveParentEdit} disabled={savingParent} className="text-sm text-white bg-green-600 hover:bg-green-700 px-3 py-1 rounded disabled:opacity-50">
                            {savingParent ? 'Saving...' : 'Save'}
                          </button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold">{parent.name}</span>
                            {parent.is_primary_contact && (
                              <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded">Primary</span>
                            )}
                            {parent.relationship_type && (
                              <span className="text-gray-500 text-sm">({parent.relationship_type})</span>
                            )}
                          </div>
                          <button onClick={() => startEditingParent(parent)} className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1">
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                            Edit
                          </button>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div>
                            <span className="text-gray-500">Phone:</span>{' '}
                            <a href={`tel:${parent.phone}`} className="text-blue-600 font-medium">{parent.phone}</a>
                          </div>
                          <div>
                            <span className="text-gray-500">Email:</span>{' '}
                            <span className="font-medium">{parent.email || '-'}</span>
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Enrollment History - ALL enrollments */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">
                Enrollment History ({allEnrollments.length})
              </h3>
              <div className="space-y-4">
                {allEnrollments.map((enrollment) => {
                  const remaining = Math.max(0, (enrollment.visits_included || 0) - (enrollment.visits_used || 0));
                  const isActive = enrollment.status === 'ACTIVE';

                  return (
                    <div
                      key={enrollment.enrollment_id}
                      className={`border rounded-lg p-4 ${isActive ? 'border-green-300 bg-green-50' : 'border-gray-200 bg-gray-50'}`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-gray-900">
                            {enrollment.batch?.name || 'No Batch'}
                          </span>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStatusBadge(enrollment.status)}`}>
                            {enrollment.status}
                          </span>
                          <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">
                            {getPlanDisplay(enrollment.plan_type)}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          {enrollment.status === 'ACTIVE' && (
                            <>
                              <button
                                onClick={() => changeEnrollmentStatus(enrollment.enrollment_id, 'PAUSED')}
                                disabled={statusSaving && statusChangeId === enrollment.enrollment_id}
                                className="text-xs px-2 py-1 border border-yellow-300 text-yellow-700 rounded hover:bg-yellow-50 disabled:opacity-50"
                              >
                                Pause
                              </button>
                              <button
                                onClick={() => changeEnrollmentStatus(enrollment.enrollment_id, 'CANCELLED')}
                                disabled={statusSaving && statusChangeId === enrollment.enrollment_id}
                                className="text-xs px-2 py-1 border border-red-300 text-red-700 rounded hover:bg-red-50 disabled:opacity-50"
                              >
                                Cancel
                              </button>
                            </>
                          )}
                          {enrollment.status === 'PAUSED' && (() => {
                            const hasRemaining = enrollment.visits_included
                              ? (enrollment.visits_included - enrollment.visits_used) > 0
                              : enrollment.end_date
                                ? new Date(enrollment.end_date) > new Date()
                                : false;
                            return hasRemaining ? (
                              <button
                                onClick={() => changeEnrollmentStatus(enrollment.enrollment_id, 'ACTIVE')}
                                disabled={statusSaving && statusChangeId === enrollment.enrollment_id}
                                className="text-xs px-2 py-1 border border-green-300 text-green-700 rounded hover:bg-green-50 disabled:opacity-50"
                              >
                                Reactivate
                              </button>
                            ) : (
                              <button
                                onClick={() => setRenewEnrollment(enrollment)}
                                className="text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                              >
                                Renew
                              </button>
                            );
                          })()}
                          {(enrollment.status === 'EXPIRED' || enrollment.status === 'CANCELLED') && (
                            <button
                              onClick={() => setRenewEnrollment(enrollment)}
                              className="text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                            >
                              Renew
                            </button>
                          )}
                          <button
                            onClick={() => startEditingEnrollment(enrollment)}
                            className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                          >
                            Edit
                          </button>
                          <span className="text-sm text-gray-500">#{enrollment.enrollment_id}</span>
                        </div>
                      </div>

                      {editingEnrollmentId === enrollment.enrollment_id ? (
                        <div className="space-y-3">
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            <div>
                              <label className="text-gray-500 text-xs block mb-1">Booked Classes</label>
                              <input type="number" value={enrollmentEditData.visits_included} onChange={e => setEnrollmentEditData({...enrollmentEditData, visits_included: e.target.value})} min="1" className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm" />
                            </div>
                            <div>
                              <label className="text-gray-500 text-xs block mb-1">Start Date</label>
                              <input type="date" value={enrollmentEditData.start_date} onChange={e => setEnrollmentEditData({...enrollmentEditData, start_date: e.target.value})} className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm" />
                            </div>
                            <div>
                              <label className="text-gray-500 text-xs block mb-1">End Date</label>
                              <input type="date" value={enrollmentEditData.end_date} onChange={e => setEnrollmentEditData({...enrollmentEditData, end_date: e.target.value})} className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm" />
                            </div>
                            <div className="flex items-end gap-2 pb-0.5">
                              <span className="text-sm text-gray-500">Attended: <strong className="text-green-700">{enrollment.visits_used}</strong></span>
                            </div>
                          </div>
                          <div>
                            <label className="text-gray-500 text-xs block mb-1">Notes</label>
                            <textarea value={enrollmentEditData.notes} onChange={e => setEnrollmentEditData({...enrollmentEditData, notes: e.target.value})} rows={2} className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm" placeholder="Enrollment notes..." />
                          </div>
                          <div className="flex gap-2 justify-end">
                            <button onClick={() => setEditingEnrollmentId(null)} className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1 border border-gray-300 rounded">Cancel</button>
                            <button onClick={saveEnrollmentEdit} disabled={savingEnrollment} className="text-sm text-white bg-green-600 hover:bg-green-700 px-3 py-1 rounded disabled:opacity-50">
                              {savingEnrollment ? 'Saving...' : 'Save'}
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                          <div>
                            <span className="text-gray-500">Period:</span>{' '}
                            <span className="font-medium">
                              {formatDate(enrollment.start_date)} - {formatDate(enrollment.end_date)}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-500">Booked:</span>{' '}
                            <span className="font-medium">{enrollment.visits_included || '-'}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">Attended:</span>{' '}
                            <span className="font-medium text-green-700">{enrollment.visits_used}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">Remaining:</span>{' '}
                            <span className={`font-medium ${remaining === 0 && isActive ? 'text-red-600' : 'text-orange-600'}`}>
                              {remaining}
                            </span>
                          </div>
                          {enrollment.days_selected && enrollment.days_selected.length > 0 && (
                            <div className="col-span-2">
                              <span className="text-gray-500">Days:</span>{' '}
                              <span className="font-medium">{enrollment.days_selected.join(', ')}</span>
                            </div>
                          )}
                          <div>
                            <span className="text-gray-500">Enrolled:</span>{' '}
                            <span className="font-medium">{formatDate(enrollment.enrolled_at)}</span>
                          </div>
                        </div>
                      )}

                      {(enrollment.total_paid > 0 || enrollment.total_discount > 0 || enrollment.payment_method) && (
                        <div className="mt-2 pt-2 border-t border-gray-200 flex gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">Paid:</span>{' '}
                            <span className="font-medium text-green-600">Rs.{enrollment.total_paid.toLocaleString()}</span>
                          </div>
                          {enrollment.payment_method && (
                            <div>
                              <span className="text-gray-500">Mode:</span>{' '}
                              <span className="font-medium">{enrollment.payment_method.replace('_', ' ')}</span>
                            </div>
                          )}
                          {enrollment.total_discount > 0 && (
                            <div>
                              <span className="text-gray-500">Discount:</span>{' '}
                              <span className="font-medium text-orange-600">Rs.{enrollment.total_discount.toLocaleString()}</span>
                            </div>
                          )}
                        </div>
                      )}

                      {enrollment.enrollment_notes && (
                        <div className="mt-2 pt-2 border-t border-gray-200 text-sm">
                          <span className="text-gray-500">Notes:</span>{' '}
                          <span className="text-gray-700">{enrollment.enrollment_notes}</span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'attendance' && (
          <div className="space-y-6">
            {/* Overall Attendance Summary */}
            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex gap-6">
                <div>
                  <span className="text-gray-500 text-sm">Total Sessions:</span>{' '}
                  <span className="font-semibold">{totalSessions}</span>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Present:</span>{' '}
                  <span className="font-semibold text-green-600">{totalPresent}</span>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Absent:</span>{' '}
                  <span className="font-semibold text-red-600">{totalAbsent}</span>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Rate:</span>{' '}
                  <span className="font-semibold text-purple-600">{overallRate}%</span>
                </div>
              </div>
            </div>

            {/* Attendance grouped by batch */}
            {Object.keys(attendanceByBatch).length === 0 ? (
              <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
                No attendance records found
              </div>
            ) : (
              Object.entries(attendanceByBatch).map(([batchName, records]) => {
                const batchPresent = records.filter(r => r.status === 'PRESENT').length;
                const batchAbsent = records.filter(r => r.status === 'ABSENT').length;
                const batchRate = records.length > 0 ? Math.round((batchPresent / records.length) * 100) : 0;

                // Find matching enrollment for this batch
                const matchingEnrollment = allEnrollments.find(e => e.batch?.name === batchName);

                return (
                  <div key={batchName} className="bg-white rounded-lg shadow">
                    {/* Batch header */}
                    <div className="p-4 border-b bg-gray-50 rounded-t-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold text-gray-900">{batchName}</h4>
                          {matchingEnrollment && (
                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStatusBadge(matchingEnrollment.status)}`}>
                              {matchingEnrollment.status}
                            </span>
                          )}
                        </div>
                        <div className="flex gap-4 text-sm">
                          <span>Sessions: <strong>{records.length}</strong></span>
                          <span className="text-green-600">Present: <strong>{batchPresent}</strong></span>
                          <span className="text-red-600">Absent: <strong>{batchAbsent}</strong></span>
                          <span className="text-purple-600">Rate: <strong>{batchRate}%</strong></span>
                        </div>
                      </div>
                    </div>

                    {/* Attendance table for this batch */}
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="text-left p-3 font-semibold text-gray-700 w-12">#</th>
                            <th className="text-left p-3 font-semibold text-gray-700">Session Date</th>
                            <th className="text-center p-3 font-semibold text-gray-700">Status</th>
                            <th className="text-left p-3 font-semibold text-gray-700">Notes</th>
                          </tr>
                        </thead>
                        <tbody>
                          {records.map((record, idx) => (
                            <tr key={record.id} className="border-b hover:bg-gray-50">
                              <td className="p-3 text-gray-500">{idx + 1}</td>
                              <td className="p-3">
                                {formatDate(record.session_date) || formatDate(record.marked_at) || '-'}
                              </td>
                              <td className="p-3 text-center">
                                <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusBadge(record.status)}`}>
                                  {record.status}
                                </span>
                              </td>
                              <td className="p-3 text-gray-600 text-sm">{record.notes || '-'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}

        {activeTab === 'progress' && (
          <div className="space-y-4">
            {skillProgress.length === 0 ? (
              <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
                No skill progress recorded yet
              </div>
            ) : (
              <>
                {/* Progress Summary Header */}
                <div className="bg-white rounded-lg shadow p-4">
                  <div className="flex items-center gap-6">
                    <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center">
                      <svg className="w-10 h-10 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                      </svg>
                    </div>
                    <div className="flex-1">
                      <div className="flex flex-wrap gap-6 text-sm">
                        <div>
                          <span className="text-gray-500">Skills Mastered:</span>{' '}
                          <span className="font-semibold">
                            {skillProgress.filter(s => s.level === 'MASTERED').length} / {skillProgress.length}
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <span className="text-gray-500">Overall Progress:</span>{' '}
                          {[1, 2, 3, 4, 5].map((star) => {
                            const mastered = skillProgress.filter(s => s.level === 'MASTERED').length;
                            const achieved = skillProgress.filter(s => s.level === 'ACHIEVED').length;
                            const total = skillProgress.length;
                            const progress = total > 0 ? ((mastered * 2 + achieved) / (total * 2)) * 5 : 0;
                            return (
                              <svg
                                key={star}
                                className={`w-5 h-5 ${star <= Math.round(progress) ? 'text-yellow-400' : 'text-gray-300'}`}
                                fill="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/>
                              </svg>
                            );
                          })}
                        </div>
                        <div>
                          <span className="text-gray-500">Last Updated:</span>{' '}
                          <span className="font-semibold">
                            {skillProgress.length > 0
                              ? formatDate(skillProgress.reduce((latest, s) =>
                                  !latest || (s.last_updated_at && s.last_updated_at > latest) ? s.last_updated_at : latest,
                                  skillProgress[0].last_updated_at
                                ))
                              : '-'
                            }
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Skills grouped by category */}
                {(() => {
                  // Group skills by category
                  const groupedSkills: Record<string, typeof skillProgress> = {};
                  skillProgress.forEach(skill => {
                    const category = skill.category || 'General';
                    if (!groupedSkills[category]) groupedSkills[category] = [];
                    groupedSkills[category].push(skill);
                  });

                  return Object.entries(groupedSkills).map(([category, skills]) => (
                    <div key={category} className="bg-white rounded-lg shadow">
                      {/* Category Header */}
                      <div className="p-4 border-b bg-gray-50 rounded-t-lg flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <input type="checkbox" className="w-4 h-4 text-blue-600 rounded" readOnly />
                          <h4 className="font-semibold text-gray-900">{category} ({skills.length})</h4>
                        </div>
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>

                      {/* Skills in this category */}
                      <div className="divide-y">
                        {skills.map((skill) => (
                          <div key={skill.id} className="p-4">
                            <div className="flex items-center justify-between mb-2">
                              <h5 className="font-medium text-gray-900">{skill.skill_name}</h5>
                              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                              </svg>
                            </div>

                            {/* Level buttons */}
                            <div className="flex gap-2 mb-3">
                              {['NOT_STARTED', 'IN_PROGRESS', 'ACHIEVED', 'MASTERED'].map((level) => {
                                const isActive = skill.level === level;
                                const labels: Record<string, string> = {
                                  'NOT_STARTED': 'Not Started',
                                  'IN_PROGRESS': 'Learning',
                                  'ACHIEVED': 'Developing',
                                  'MASTERED': 'Mastered'
                                };
                                return (
                                  <div
                                    key={level}
                                    className={`px-3 py-1.5 rounded-full text-sm flex items-center gap-1 ${
                                      isActive
                                        ? level === 'MASTERED'
                                          ? 'bg-green-100 text-green-800 border-2 border-green-500'
                                          : level === 'ACHIEVED'
                                          ? 'bg-blue-100 text-blue-800 border-2 border-blue-500'
                                          : level === 'IN_PROGRESS'
                                          ? 'bg-yellow-100 text-yellow-800 border-2 border-yellow-500'
                                          : 'bg-gray-100 text-gray-600 border-2 border-gray-400'
                                        : 'bg-gray-50 text-gray-500 border border-gray-200'
                                    }`}
                                  >
                                    {isActive && (
                                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                      </svg>
                                    )}
                                    {labels[level]}
                                  </div>
                                );
                              })}
                            </div>

                            {/* Notes and last update */}
                            {skill.notes && (
                              <div className="text-sm text-gray-600 italic mb-1">
                                Coach Note: &quot;{skill.notes}&quot;
                              </div>
                            )}
                            <div className="text-xs text-gray-400">
                              Last Update: {formatDate(skill.last_updated_at)}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ));
                })()}
              </>
            )}
          </div>
        )}
      </div>

      {/* Renewal Modal */}
      {renewEnrollment && childInfo && (
        <RenewFromProfileModal
          enrollment={renewEnrollment}
          child={childInfo}
          parents={parents}
          centerId={centerId}
          onClose={() => setRenewEnrollment(null)}
          onSuccess={() => {
            setRenewEnrollment(null);
            fetchStudentData();
          }}
        />
      )}
    </>
  );
}


// ─── Renewal Modal (used from Student Profile) ─────────────────────────────
const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const PLAN_TYPES = [
  { value: 'MONTHLY', label: 'Monthly' },
  { value: 'QUARTERLY', label: 'Quarterly' },
  { value: 'YEARLY', label: 'Yearly' },
  { value: 'PAY_PER_VISIT', label: 'Pay Per Visit' },
  { value: 'WEEKLY', label: 'Weekly' },
  { value: 'CUSTOM', label: 'Custom' },
];
const PAYMENT_METHODS = [
  { value: 'CASH', label: 'Cash' },
  { value: 'UPI', label: 'UPI' },
  { value: 'CARD', label: 'Card' },
  { value: 'BANK_TRANSFER', label: 'Bank Transfer' },
  { value: 'OTHER', label: 'Other' },
];

interface RenewBatch {
  id: number;
  name: string;
  age_min?: number;
  age_max?: number;
  days_of_week?: string[];
  start_time?: string;
  end_time?: string;
}

function RenewFromProfileModal({
  enrollment,
  child,
  parents,
  centerId,
  onClose,
  onSuccess,
}: {
  enrollment: EnrolledStudent;
  child: Child;
  parents: Parent[];
  centerId: number;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [batches, setBatches] = useState<RenewBatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Form state pre-filled from previous enrollment
  const [batchId, setBatchId] = useState<number | ''>(enrollment.batch?.id || '');
  const [daysSelected, setDaysSelected] = useState<string[]>(enrollment.days_selected || enrollment.batch?.days_of_week || []);
  const [planType, setPlanType] = useState(enrollment.plan_type || 'MONTHLY');
  const [bookedClasses, setBookedClasses] = useState(enrollment.visits_included ? String(enrollment.visits_included) : '');
  const [startDate, setStartDate] = useState(() => {
    if (enrollment.end_date) {
      const next = new Date(enrollment.end_date);
      next.setDate(next.getDate() + 1);
      return next.toISOString().split('T')[0];
    }
    return new Date().toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState('');
  const [totalAmount, setTotalAmount] = useState('');
  const [paidAmount, setPaidAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('CASH');
  const [paymentRef, setPaymentRef] = useState('');
  const [notes, setNotes] = useState('');

  const age = child.dob ? (() => {
    const today = new Date();
    const birth = new Date(child.dob!);
    let a = today.getFullYear() - birth.getFullYear();
    const m = today.getMonth() - birth.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) a--;
    return a;
  })() : child.age_years;

  const primaryParent = parents.find(p => p.is_primary_contact) || parents[0];

  useEffect(() => {
    fetchBatches();
  }, []);

  // Auto-fill days when batch changes
  useEffect(() => {
    if (batchId) {
      const batch = batches.find(b => b.id === batchId);
      if (batch?.days_of_week) {
        setDaysSelected(batch.days_of_week);
      }
    }
  }, [batchId, batches]);

  // Auto-calculate end date and booked classes
  useEffect(() => {
    if (startDate && planType !== 'PAY_PER_VISIT' && planType !== 'CUSTOM') {
      const start = new Date(startDate);
      const end = new Date(start);
      const daysPerWeek = Math.max(daysSelected.length, 1);
      let weeks = 1;
      switch (planType) {
        case 'WEEKLY': weeks = 1; end.setDate(end.getDate() + 7); break;
        case 'MONTHLY': weeks = 4; end.setMonth(end.getMonth() + 1); break;
        case 'QUARTERLY': weeks = 12; end.setMonth(end.getMonth() + 3); break;
        case 'YEARLY': weeks = 48; end.setFullYear(end.getFullYear() + 1); break;
      }
      setEndDate(end.toISOString().split('T')[0]);
      setBookedClasses(String(daysPerWeek * weeks));
    }
  }, [startDate, planType, daysSelected.length]);

  const fetchBatches = async () => {
    try {
      const params = new URLSearchParams({ active_only: 'true', center_id: centerId.toString() });
      const data = await api.get<RenewBatch[]>(`/api/v1/enrollments/batches?${params}`);
      setBatches(data);
    } catch {
      console.error('Failed to fetch batches');
    }
  };

  const toggleDay = (day: string) => {
    setDaysSelected(prev =>
      prev.includes(day) ? prev.filter(d => d !== day) : [...prev, day]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!batchId) { setError('Please select a batch'); return; }
    if (!bookedClasses || parseInt(bookedClasses) <= 0) { setError('Booked classes is required'); return; }
    if (!totalAmount || parseFloat(totalAmount) <= 0) { setError('Total amount is required'); return; }
    if (!paidAmount) { setError('Paid amount is required'); return; }

    setLoading(true);
    try {
      const payload = {
        child_id: child.id,
        batch_id: batchId,
        plan_type: planType,
        start_date: startDate || null,
        end_date: endDate || null,
        visits_included: bookedClasses ? parseInt(bookedClasses) : null,
        days_selected: daysSelected.length > 0 ? daysSelected : null,
        notes: notes || null,
        payment: {
          amount: parseFloat(paidAmount),
          method: paymentMethod,
          reference: paymentRef || null,
          paid_at: new Date().toISOString(),
        },
      };
      await api.post(`/api/v1/enrollments?center_id=${centerId}`, payload);
      setSuccess(true);
      setTimeout(() => onSuccess(), 1200);
    } catch (err: any) {
      setError(err.message || 'Failed to create renewal');
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-blue-600 text-white p-4 flex items-center justify-between rounded-t-lg">
          <div>
            <h2 className="text-lg font-bold">Renew Enrollment</h2>
            <p className="text-blue-100 text-sm">
              {child.enquiry_id && <span className="font-mono mr-2">{child.enquiry_id}</span>}
              {child.first_name} {child.last_name || ''}
            </p>
          </div>
          <button onClick={onClose} className="text-white hover:text-blue-200 text-2xl" disabled={loading}>
            &times;
          </button>
        </div>

        {/* Auto-populated student info (read-only) */}
        <div className="px-6 pt-4 pb-2">
          <div className="bg-gray-50 rounded-lg p-3 text-sm space-y-1">
            <div className="flex justify-between">
              <span className="text-gray-500">Student:</span>
              <span className="font-medium">{child.first_name} {child.last_name || ''}</span>
            </div>
            {child.enquiry_id && (
              <div className="flex justify-between">
                <span className="text-gray-500">TLG ID:</span>
                <span className="font-medium font-mono">{child.enquiry_id}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-gray-500">DOB / Age:</span>
              <span className="font-medium">
                {child.dob
                  ? `${new Date(child.dob).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })} (${age} yrs)`
                  : age ? `${age} years` : '-'}
              </span>
            </div>
            {primaryParent && (
              <div className="flex justify-between">
                <span className="text-gray-500">Parent:</span>
                <span className="font-medium">{primaryParent.name} ({primaryParent.phone})</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-gray-500">Previous Plan:</span>
              <span className="font-medium">
                {getPlanDisplay(enrollment.plan_type)} — {enrollment.batch?.name || 'No batch'}
                {enrollment.visits_included ? ` · ${enrollment.visits_used}/${enrollment.visits_included} classes` : ''}
              </span>
            </div>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-auto px-6 pb-6">
          <div className="space-y-4 mt-3">
            {/* Batch */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Batch <span className="text-red-500">*</span>
              </label>
              <select
                value={batchId}
                onChange={e => setBatchId(e.target.value ? parseInt(e.target.value) : '')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="">Select Batch</option>
                {batches.map(b => (
                  <option key={b.id} value={b.id}>
                    {b.name} {b.age_min && b.age_max ? `(${b.age_min}-${b.age_max} yrs)` : ''}
                    {b.days_of_week ? ` - ${b.days_of_week.join(', ')}` : ''}
                  </option>
                ))}
              </select>
            </div>

            {/* Days */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Class Days</label>
              <div className="flex flex-wrap gap-2">
                {DAYS.map(day => (
                  <button
                    key={day}
                    type="button"
                    onClick={() => toggleDay(day)}
                    className={`px-3 py-1.5 text-sm font-medium rounded-lg border transition ${
                      daysSelected.includes(day)
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {day}
                  </button>
                ))}
              </div>
            </div>

            {/* Duration + Booked Classes */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Duration <span className="text-red-500">*</span>
                </label>
                <select
                  value={planType}
                  onChange={e => setPlanType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {PLAN_TYPES.map(p => (
                    <option key={p.value} value={p.value}>{p.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Booked Classes <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  value={bookedClasses}
                  onChange={e => setBookedClasses(e.target.value)}
                  placeholder="e.g. 24"
                  min="1"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Start Date + End Date */}
            <div className="grid grid-cols-2 gap-4">
              <DateInput label="Start Date" value={startDate} onChange={setStartDate} required />
              <DateInput label="End Date" value={endDate} onChange={setEndDate} min={startDate} required />
            </div>

            {/* Total Amount + Paid Amount */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Total Amount (Rs.) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  value={totalAmount}
                  onChange={e => {
                    setTotalAmount(e.target.value);
                    if (!paidAmount) setPaidAmount(e.target.value);
                  }}
                  placeholder="0"
                  min="0"
                  step="0.01"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Paid Amount (Rs.) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  value={paidAmount}
                  onChange={e => setPaidAmount(e.target.value)}
                  placeholder="0"
                  min="0"
                  step="0.01"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Payment Mode + Reference */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Payment Mode <span className="text-red-500">*</span>
                </label>
                <select
                  value={paymentMethod}
                  onChange={e => setPaymentMethod(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {PAYMENT_METHODS.map(m => (
                    <option key={m.value} value={m.value}>{m.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Reference / Txn ID</label>
                <input
                  type="text"
                  value={paymentRef}
                  onChange={e => setPaymentRef(e.target.value)}
                  placeholder="Optional"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
              <textarea
                value={notes}
                onChange={e => setNotes(e.target.value)}
                rows={2}
                placeholder="Optional renewal notes..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">{error}</div>
            )}
            {success && (
              <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm">
                Renewal created successfully!
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="mt-6 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || success}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {loading && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>}
              {loading ? 'Creating...' : 'Create Renewal'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
