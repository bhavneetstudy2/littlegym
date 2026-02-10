'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useCenter } from '@/contexts/CenterContext';
import { api } from '@/lib/api';
import StudentProfileModal from '@/components/StudentProfileModal';

// Types
interface Child {
  id: number;
  enquiry_id?: string;
  first_name: string;
  last_name?: string;
  dob?: string;
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
}

interface ClassSession {
  id: number;
  batch_id: number;
  session_date: string;
  start_time?: string;
  end_time?: string;
  trainer_user_id?: number;
  status: string;
}

interface AttendanceRecord {
  child_id: number;
  status: string;
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

const formatTime = (timeString?: string) => {
  if (!timeString) return '';
  return timeString.substring(0, 5);
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
    'CANCELLED': 'bg-gray-100 text-gray-800'
  };
  return styles[status] || 'bg-gray-100 text-gray-800';
};

const getPlanDisplay = (planType: string) => {
  const types: Record<string, string> = {
    'PAY_PER_VISIT': 'Per Visit',
    'WEEKLY': 'Weekly',
    'MONTHLY': 'Monthly',
    'QUARTERLY': 'Quarterly',
    'YEARLY': 'Yearly',
    'CUSTOM': 'Custom'
  };
  return types[planType] || planType;
};

const getBatchBadgeColor = (batchName: string) => {
  const colors: Record<string, string> = {
    'Giggle Worms': 'bg-pink-100 text-pink-700',
    'Funny Bugs': 'bg-orange-100 text-orange-700',
    'Good Friends': 'bg-blue-100 text-blue-700',
    'Super Beasts': 'bg-red-100 text-red-700',
    'Grade School': 'bg-indigo-100 text-indigo-700',
  };
  return colors[batchName] || 'bg-gray-100 text-gray-700';
};

// Attendance Modal Component
function AttendanceModal({
  batch,
  students,
  onClose,
  onSave,
  centerId
}: {
  batch: BatchInfo;
  students: EnrolledStudent[];
  onClose: () => void;
  onSave: () => void;
  centerId: number;
}) {
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [attendance, setAttendance] = useState<Record<number, { status: string; notes: string }>>({});
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Initialize attendance for all students
  useEffect(() => {
    const initialAttendance: Record<number, { status: string; notes: string }> = {};
    students.forEach(student => {
      initialAttendance[student.child.id] = { status: 'PRESENT', notes: '' };
    });
    setAttendance(initialAttendance);
  }, [students]);

  const handleStatusChange = (childId: number, status: string) => {
    setAttendance(prev => ({
      ...prev,
      [childId]: { ...prev[childId], status }
    }));
  };

  const handleNotesChange = (childId: number, notes: string) => {
    setAttendance(prev => ({
      ...prev,
      [childId]: { ...prev[childId], notes }
    }));
  };

  const handleMarkAll = (status: string) => {
    const updated: Record<number, { status: string; notes: string }> = {};
    students.forEach(student => {
      updated[student.child.id] = { ...attendance[student.child.id], status };
    });
    setAttendance(updated);
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);

    try {
      const records = Object.entries(attendance).map(([childId, data]) => ({
        child_id: Number(childId),
        status: data.status,
        notes: data.notes || null
      }));

      // Use quick-mark endpoint that auto-creates session
      await api.post(`/api/v1/attendance/quick-mark?center_id=${centerId}`, {
        batch_id: batch.id,
        session_date: selectedDate,
        attendances: records
      });

      setMessage({ type: 'success', text: `✓ Attendance saved for ${records.length} students!` });

      // Wait a moment to show success message, then close and refresh
      setTimeout(() => {
        onSave();
        onClose();
      }, 1500);
    } catch (error: any) {
      console.error('Attendance error:', error);

      // User-friendly error messages
      if (error.response?.status === 401) {
        setMessage({
          type: 'error',
          text: '⚠ Your session expired. Please refresh the page and login again.'
        });
      } else if (error.response?.status === 403) {
        setMessage({
          type: 'error',
          text: '⚠ You don\'t have permission to mark attendance. Contact your administrator.'
        });
      } else if (error.response?.status === 404) {
        setMessage({
          type: 'error',
          text: '⚠ Batch not found. Please refresh the page and try again.'
        });
      } else {
        setMessage({
          type: 'error',
          text: `⚠ ${error.response?.data?.detail || 'Failed to save attendance. Please try again.'}`
        });
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-4 border-b bg-green-50">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-900">Mark Attendance</h2>
              <p className="text-sm text-gray-600">{batch.name}</p>
            </div>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
          </div>
        </div>

        {/* Date Selection & Quick Actions */}
        <div className="p-4 bg-gray-50 border-b">
          <div className="flex flex-wrap gap-4 items-center justify-between">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Class Date</label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleMarkAll('PRESENT')}
                className="px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 text-sm font-medium transition"
              >
                ✓ Mark All Present
              </button>
              <button
                onClick={() => handleMarkAll('ABSENT')}
                className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 text-sm font-medium transition"
              >
                ✗ Mark All Absent
              </button>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Select date and mark students as present or absent. Click Save when done.
          </p>
        </div>

        {message && (
          <div className={`mx-4 mt-4 p-3 rounded-lg ${message.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
            {message.text}
          </div>
        )}

        {/* Attendance Table */}
        <div className="flex-1 overflow-auto p-4">
          <table className="w-full border-collapse">
            <thead className="bg-gray-100 sticky top-0">
              <tr>
                <th className="text-left p-3 border-b font-semibold">#</th>
                <th className="text-left p-3 border-b font-semibold">Student Name</th>
                <th className="text-left p-3 border-b font-semibold">Parent</th>
                <th className="text-center p-3 border-b font-semibold">Status</th>
                <th className="text-left p-3 border-b font-semibold">Notes</th>
              </tr>
            </thead>
            <tbody>
              {students.map((student, index) => (
                <tr key={student.child.id} className="hover:bg-gray-50">
                  <td className="p-3 border-b text-gray-500">{index + 1}</td>
                  <td className="p-3 border-b">
                    <div className="font-medium">{student.child.first_name} {student.child.last_name || ''}</div>
                    <div className="text-sm text-gray-500">
                      {student.child.enquiry_id && <span className="text-blue-600 mr-2">{student.child.enquiry_id}</span>}
                      {calculateAge(student.child.dob) ? `${calculateAge(student.child.dob)} yrs` : ''}
                    </div>
                  </td>
                  <td className="p-3 border-b">
                    {student.parents[0] && (
                      <div className="text-sm">
                        <div>{student.parents[0].name}</div>
                        <div className="text-blue-600">{student.parents[0].phone}</div>
                      </div>
                    )}
                  </td>
                  <td className="p-3 border-b">
                    <div className="flex justify-center gap-1">
                      {['PRESENT', 'ABSENT', 'MAKEUP'].map(status => (
                        <button
                          key={status}
                          onClick={() => handleStatusChange(student.child.id, status)}
                          className={`px-3 py-1 rounded text-xs font-medium transition ${
                            attendance[student.child.id]?.status === status
                              ? status === 'PRESENT'
                                ? 'bg-green-600 text-white'
                                : status === 'ABSENT'
                                ? 'bg-red-600 text-white'
                                : 'bg-yellow-600 text-white'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                        >
                          {status === 'PRESENT' ? 'P' : status === 'ABSENT' ? 'A' : 'M'}
                        </button>
                      ))}
                    </div>
                  </td>
                  <td className="p-3 border-b">
                    <input
                      type="text"
                      value={attendance[student.child.id]?.notes || ''}
                      onChange={(e) => handleNotesChange(student.child.id, e.target.value)}
                      placeholder="Notes..."
                      className="w-full px-2 py-1 text-sm border border-gray-200 rounded focus:ring-1 focus:ring-green-500"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="p-4 border-t bg-gray-50 flex justify-between items-center">
          <div className="text-sm text-gray-600">
            <span className="font-medium">{students.length}</span> students in {batch.name}
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              disabled={saving}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving || Object.keys(attendance).length === 0}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition"
            >
              {saving ? '⏳ Saving...' : '✓ Save Attendance'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Main Page Component
export default function StudentsPage() {
  const router = useRouter();
  const { selectedCenter } = useCenter();

  const [students, setStudents] = useState<EnrolledStudent[]>([]);
  const [batches, setBatches] = useState<BatchInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ACTIVE');
  const [batchFilter, setBatchFilter] = useState<string>('');

  // View mode
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table');

  // Modals
  const [attendanceBatch, setAttendanceBatch] = useState<BatchInfo | null>(null);
  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(null);
  const [selectedEnrollmentId, setSelectedEnrollmentId] = useState<number | null>(null);
  const [showAttendanceMenu, setShowAttendanceMenu] = useState(false);

  // Debounce search query (400ms)
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchQuery), 400);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Fetch data - server-side filtering
  const fetchData = useCallback(async () => {
    if (!selectedCenter) return;

    setLoading(true);
    setError(null);

    try {
      let url = `/api/v1/enrollments/students?center_id=${selectedCenter.id}&limit=200`;
      if (statusFilter) url += `&status=${statusFilter}`;
      if (batchFilter) url += `&batch_id=${batchFilter}`;
      if (debouncedSearch.trim().length >= 2) url += `&search=${encodeURIComponent(debouncedSearch.trim())}`;

      const [studentsRes, batchesRes] = await Promise.all([
        api.get<EnrolledStudent[]>(url),
        api.get<BatchInfo[]>(`/api/v1/enrollments/batches?center_id=${selectedCenter.id}`)
      ]);

      setStudents(studentsRes);
      setBatches(batchesRes);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load students');
    } finally {
      setLoading(false);
    }
  }, [selectedCenter, statusFilter, batchFilter, debouncedSearch]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // All filtering is now server-side
  const filteredStudents = students;

  // Get students by batch for attendance
  const getStudentsByBatch = (batchId: number) => {
    return students.filter(s => s.batch?.id === batchId && s.status === 'ACTIVE');
  };

  // Handle attendance save success
  const handleAttendanceSave = () => {
    // Refresh data to show updated visits_used counts
    fetchData();
  };

  if (!selectedCenter) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500 mb-4">Please select a center first</p>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading enrolled students...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <button
                onClick={() => router.push('/dashboard')}
                className="mr-3 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Enrolled Students</h1>
                <p className="text-sm text-gray-500">{selectedCenter.name} - {filteredStudents.length} students</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {/* Attendance Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setShowAttendanceMenu(!showAttendanceMenu)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                  Mark Attendance
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {showAttendanceMenu && (
                  <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-10">
                    <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase">Select Batch</div>
                    {batches.map(batch => {
                      const batchStudents = getStudentsByBatch(batch.id);
                      return (
                        <button
                          key={batch.id}
                          onClick={() => {
                            setAttendanceBatch(batch);
                            setShowAttendanceMenu(false);
                          }}
                          disabled={batchStudents.length === 0}
                          className={`w-full text-left px-4 py-2 hover:bg-gray-50 transition flex items-center justify-between ${
                            batchStudents.length === 0 ? 'opacity-50 cursor-not-allowed' : ''
                          }`}
                        >
                          <span className="font-medium">{batch.name}</span>
                          <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                            {batchStudents.length}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* View Mode Toggle */}
              <button
                onClick={() => setViewMode('table')}
                className={`p-2 rounded-lg ${viewMode === 'table' ? 'bg-green-100 text-green-700' : 'text-gray-400 hover:text-gray-600'}`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
              <button
                onClick={() => setViewMode('cards')}
                className={`p-2 rounded-lg ${viewMode === 'cards' ? 'bg-green-100 text-green-700' : 'text-gray-400 hover:text-gray-600'}`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Filters & Batch Attendance */}
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="bg-white rounded-lg shadow p-4 mb-4">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
              <input
                type="text"
                placeholder="Search by name or phone..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              >
                <option value="">All Status</option>
                <option value="ACTIVE">Active</option>
                <option value="EXPIRED">Expired</option>
                <option value="PAUSED">Paused</option>
                <option value="CANCELLED">Cancelled</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Batch</label>
              <select
                value={batchFilter}
                onChange={(e) => setBatchFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              >
                <option value="">All Batches</option>
                {batches.map(batch => (
                  <option key={batch.id} value={batch.id}>{batch.name}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Batch Overview Cards - Click to Filter */}
        {batches.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
            {batches.map((batch) => {
              const batchCount = students.filter(s => s.batch?.id === batch.id).length;
              return (
                <div
                  key={batch.id}
                  onClick={() => setBatchFilter(batchFilter === batch.id.toString() ? '' : batch.id.toString())}
                  className={`p-3 rounded-lg shadow cursor-pointer transition ${
                    batchFilter === batch.id.toString()
                      ? 'bg-green-100 border-2 border-green-500'
                      : 'bg-white hover:shadow-md'
                  }`}
                >
                  <h3 className="font-semibold text-gray-900 text-sm">{batch.name}</h3>
                  <p className="text-xs text-gray-500">Ages {batch.age_min}-{batch.age_max}</p>
                  <p className="text-lg font-bold text-green-600 mt-1">{batchCount}</p>
                </div>
              );
            })}
          </div>
        )}

        {error && (
          <div className="bg-red-100 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {/* Students Table View */}
        {viewMode === 'table' ? (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="text-left p-3 border-b font-semibold text-gray-700">#</th>
                    <th className="text-left p-3 border-b font-semibold text-gray-700">Student Name</th>
                    <th className="text-left p-3 border-b font-semibold text-gray-700">Age</th>
                    <th className="text-left p-3 border-b font-semibold text-gray-700">Parent / Phone</th>
                    <th className="text-left p-3 border-b font-semibold text-gray-700">Batch</th>
                    <th className="text-left p-3 border-b font-semibold text-gray-700">Plan</th>
                    <th className="text-left p-3 border-b font-semibold text-gray-700">Days</th>
                    <th className="text-left p-3 border-b font-semibold text-gray-700">Validity</th>
                    <th className="text-left p-3 border-b font-semibold text-gray-700">Visits</th>
                    <th className="text-left p-3 border-b font-semibold text-gray-700">Paid</th>
                    <th className="text-center p-3 border-b font-semibold text-gray-700">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredStudents.map((student, index) => {
                    const primaryParent = student.parents.find(p => p.is_primary_contact) || student.parents[0];
                    const age = calculateAge(student.child.dob);

                    return (
                      <tr key={student.enrollment_id} className="hover:bg-gray-50 border-b cursor-pointer" onClick={() => { setSelectedStudentId(student.child.id); setSelectedEnrollmentId(student.enrollment_id); }}>
                        <td className="p-3 text-gray-500">{index + 1}</td>
                        <td className="p-3">
                          <div className="font-medium text-blue-600 hover:text-blue-800">
                            {student.child.first_name} {student.child.last_name || ''}
                          </div>
                          <div className="text-xs text-gray-500">
                            {student.child.enquiry_id && <span className="text-blue-500 mr-1">{student.child.enquiry_id}</span>}
                            {student.child.school && <span>{student.child.school}</span>}
                          </div>
                        </td>
                        <td className="p-3 text-gray-600">
                          {age ? `${age} yrs` : '-'}
                        </td>
                        <td className="p-3">
                          {primaryParent ? (
                            <div>
                              <div className="text-sm font-medium">{primaryParent.name}</div>
                              <div className="text-sm text-blue-600">{primaryParent.phone}</div>
                            </div>
                          ) : '-'}
                        </td>
                        <td className="p-3">
                          {student.batch ? (
                            <span className={`px-2 py-1 rounded text-sm ${getBatchBadgeColor(student.batch.name)}`}>
                              {student.batch.name}
                            </span>
                          ) : '-'}
                        </td>
                        <td className="p-3">
                          <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-sm">
                            {getPlanDisplay(student.plan_type)}
                          </span>
                        </td>
                        <td className="p-3 text-sm text-gray-600">
                          {student.days_selected?.join(', ') || '-'}
                        </td>
                        <td className="p-3 text-sm">
                          {student.plan_type === 'PAY_PER_VISIT' ? (
                            <span className="text-gray-600">N/A</span>
                          ) : (
                            <div>
                              <div>{formatDate(student.start_date)}</div>
                              <div className="text-gray-500">to {formatDate(student.end_date)}</div>
                            </div>
                          )}
                        </td>
                        <td className="p-3 text-center">
                          {student.plan_type === 'PAY_PER_VISIT' ? (
                            <div>
                              <span className="font-medium">{student.visits_used}</span>
                              <span className="text-gray-400">/{student.visits_included || '?'}</span>
                            </div>
                          ) : '-'}
                        </td>
                        <td className="p-3">
                          <span className="font-medium text-green-600">
                            ₹{student.total_paid?.toLocaleString() || 0}
                          </span>
                        </td>
                        <td className="p-3 text-center">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(student.status)}`}>
                            {student.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {filteredStudents.length === 0 && (
              <div className="p-8 text-center text-gray-500">
                No students found matching your filters
              </div>
            )}
          </div>
        ) : (
          /* Cards View */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredStudents.map((student) => {
              const primaryParent = student.parents.find(p => p.is_primary_contact) || student.parents[0];
              const age = calculateAge(student.child.dob);

              return (
                <div key={student.enrollment_id} className="bg-white rounded-lg shadow p-4 cursor-pointer hover:shadow-lg transition" onClick={() => { setSelectedStudentId(student.child.id); setSelectedEnrollmentId(student.enrollment_id); }}>
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-blue-600 hover:text-blue-800">
                        {student.child.first_name} {student.child.last_name || ''}
                      </h3>
                      <p className="text-sm text-gray-500">
                        {student.child.enquiry_id && <span className="text-blue-500 mr-1">{student.child.enquiry_id}</span>}
                        {age ? `${age} years` : ''} {student.child.school ? `| ${student.child.school}` : ''}
                      </p>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(student.status)}`}>
                      {student.status}
                    </span>
                  </div>

                  {primaryParent && (
                    <div className="mb-3 text-sm">
                      <span className="text-gray-500">Parent:</span>{' '}
                      <span className="font-medium">{primaryParent.name}</span>
                      <span className="text-blue-600 ml-2">{primaryParent.phone}</span>
                    </div>
                  )}

                  <div className="flex flex-wrap gap-2 mb-3">
                    {student.batch && (
                      <span className={`px-2 py-1 rounded text-xs ${getBatchBadgeColor(student.batch.name)}`}>
                        {student.batch.name}
                      </span>
                    )}
                    <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs">
                      {getPlanDisplay(student.plan_type)}
                    </span>
                  </div>

                  <div className="text-sm text-gray-500 pt-3 border-t">
                    {student.plan_type === 'PAY_PER_VISIT' ? (
                      <span>Visits: {student.visits_used}/{student.visits_included || '?'}</span>
                    ) : (
                      <span>{formatDate(student.start_date)} - {formatDate(student.end_date)}</span>
                    )}
                    <span className="float-right text-green-600 font-medium">
                      ₹{student.total_paid?.toLocaleString() || 0}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Attendance Modal */}
      {attendanceBatch && (
        <AttendanceModal
          batch={attendanceBatch}
          students={getStudentsByBatch(attendanceBatch.id)}
          onClose={() => setAttendanceBatch(null)}
          onSave={handleAttendanceSave}
          centerId={selectedCenter.id}
        />
      )}

      {/* Student Profile Modal */}
      {selectedStudentId && (
        <StudentProfileModal
          childId={selectedStudentId}
          enrollmentId={selectedEnrollmentId || undefined}
          centerId={selectedCenter.id}
          onClose={() => { setSelectedStudentId(null); setSelectedEnrollmentId(null); }}
        />
      )}
    </div>
  );
}
