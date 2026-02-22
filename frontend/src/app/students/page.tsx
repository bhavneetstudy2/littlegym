'use client';

import { useState, useEffect } from 'react';
import { useCenter } from '@/contexts/CenterContext';
import { api } from '@/lib/api';
import StudentProfileModal from '@/components/StudentProfileModal';

interface Child {
  id: number;
  enquiry_id?: string;
  first_name: string;
  last_name?: string;
  dob?: string;
  age_years?: number;
  school?: string;
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

interface MasterStudent {
  child: Child;
  parents: Parent[];
  enrollment_count: number;
  is_renewal: boolean;
  latest_enrollment_id: number;
  latest_plan_type: string;
  latest_status: string;
  latest_start_date?: string;
  latest_end_date?: string;
  latest_visits_included?: number;
  latest_visits_used: number;
  latest_batch?: BatchInfo;
  latest_enrolled_at?: string;
  total_paid: number;
  lead_source?: string;
  converted_at?: string;
}

interface MasterStudentsResponse {
  students: MasterStudent[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface StatsResponse {
  total: number;
  new_count: number;
  renewal_count: number;
  by_status: Record<string, number>;
}

interface Batch {
  id: number;
  name: string;
  active: boolean;
}

const formatDate = (dateString?: string) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
};

const calculateAge = (dob?: string, ageYears?: number) => {
  if (dob) {
    const today = new Date();
    const birthDate = new Date(dob);
    let age = today.getFullYear() - birthDate.getFullYear();
    const m = today.getMonth() - birthDate.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) age--;
    return age;
  }
  return ageYears || null;
};

const getPlanDisplay = (planType: string) => {
  const types: Record<string, string> = {
    PAY_PER_VISIT: 'Per Visit',
    WEEKLY: 'Weekly',
    MONTHLY: 'Monthly',
    QUARTERLY: 'Quarterly',
    YEARLY: 'Yearly',
    CUSTOM: 'Custom',
  };
  return types[planType] || planType;
};

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    ACTIVE: 'bg-green-100 text-green-800',
    EXPIRED: 'bg-red-100 text-red-800',
    CANCELLED: 'bg-gray-100 text-gray-800',
    PAUSED: 'bg-yellow-100 text-yellow-800',
  };
  return colors[status] || 'bg-gray-100 text-gray-800';
};

export default function MasterStudentsPage() {
  const { selectedCenter } = useCenter();
  const [students, setStudents] = useState<MasterStudent[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [batches, setBatches] = useState<Batch[]>([]);

  // Filters
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedBatch, setSelectedBatch] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('');

  // Pagination
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [total, setTotal] = useState(0);
  const pageSize = 50;

  // Modal
  const [selectedChildId, setSelectedChildId] = useState<number | null>(null);
  const [showProfile, setShowProfile] = useState(false);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 400);
    return () => clearTimeout(timer);
  }, [search]);

  // Fetch stats
  useEffect(() => {
    if (selectedCenter) {
      fetchStats();
      fetchBatches();
    }
  }, [selectedCenter]);

  // Fetch students when filters change
  useEffect(() => {
    if (selectedCenter) {
      fetchStudents();
    }
  }, [selectedCenter, page, debouncedSearch, selectedStatus, selectedBatch, selectedType]);

  const fetchStats = async () => {
    if (!selectedCenter) return;
    try {
      const params = new URLSearchParams({ center_id: selectedCenter.id.toString() });
      const data = await api.get<StatsResponse>(
        `/api/v1/enrollments/master-students/stats?${params}`
      );
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  const fetchBatches = async () => {
    if (!selectedCenter) return;
    try {
      const params = new URLSearchParams({
        center_id: selectedCenter.id.toString(),
        active_only: 'true',
      });
      const data = await api.get<Batch[]>(`/api/v1/enrollments/batches?${params}`);
      setBatches(data);
    } catch (err) {
      console.error('Failed to fetch batches:', err);
    }
  };

  const fetchStudents = async () => {
    if (!selectedCenter) return;
    setLoading(true);
    try {
      const params = new URLSearchParams({
        center_id: selectedCenter.id.toString(),
        page: page.toString(),
        page_size: pageSize.toString(),
      });
      if (debouncedSearch) params.append('search', debouncedSearch);
      if (selectedStatus) params.append('enrollment_status', selectedStatus);
      if (selectedBatch) params.append('batch_id', selectedBatch);
      if (selectedType) params.append('enrollment_type', selectedType);

      const data = await api.get<MasterStudentsResponse>(
        `/api/v1/enrollments/master-students/list?${params}`
      );
      setStudents(data.students);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error('Failed to fetch students:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRowClick = (student: MasterStudent) => {
    setSelectedChildId(student.child.id);
    setShowProfile(true);
  };

  if (!selectedCenter) {
    return (
      <div className="p-8 bg-gray-50 min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Please select a center first</p>
      </div>
    );
  }

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Students</h1>
          <p className="text-gray-600 mt-1">
            All enrolled students at {selectedCenter.name}
          </p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <div
              className={`bg-white rounded-xl shadow-sm border-2 p-4 cursor-pointer transition ${
                selectedType === '' ? 'border-blue-500' : 'border-gray-200 hover:border-blue-300'
              }`}
              onClick={() => { setSelectedType(''); setPage(1); }}
            >
              <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
              <div className="text-sm text-gray-600">Total Students</div>
            </div>
            <div
              className={`bg-white rounded-xl shadow-sm border-2 p-4 cursor-pointer transition ${
                selectedType === 'new' ? 'border-green-500' : 'border-gray-200 hover:border-green-300'
              }`}
              onClick={() => { setSelectedType(selectedType === 'new' ? '' : 'new'); setPage(1); }}
            >
              <div className="text-2xl font-bold text-green-600">{stats.new_count}</div>
              <div className="text-sm text-gray-600">New Enrollments</div>
            </div>
            <div
              className={`bg-white rounded-xl shadow-sm border-2 p-4 cursor-pointer transition ${
                selectedType === 'renewal' ? 'border-blue-500' : 'border-gray-200 hover:border-blue-300'
              }`}
              onClick={() => { setSelectedType(selectedType === 'renewal' ? '' : 'renewal'); setPage(1); }}
            >
              <div className="text-2xl font-bold text-blue-600">{stats.renewal_count}</div>
              <div className="text-sm text-gray-600">Renewals</div>
            </div>
            <div
              className={`bg-white rounded-xl shadow-sm border-2 p-4 cursor-pointer transition ${
                selectedStatus === 'ACTIVE' ? 'border-green-500' : 'border-gray-200 hover:border-green-300'
              }`}
              onClick={() => { setSelectedStatus(selectedStatus === 'ACTIVE' ? '' : 'ACTIVE'); setPage(1); }}
            >
              <div className="text-2xl font-bold text-green-700">{stats.by_status?.ACTIVE || 0}</div>
              <div className="text-sm text-gray-600">Active</div>
            </div>
            <div
              className={`bg-white rounded-xl shadow-sm border-2 p-4 cursor-pointer transition ${
                selectedStatus === 'EXPIRED' ? 'border-red-500' : 'border-gray-200 hover:border-red-300'
              }`}
              onClick={() => { setSelectedStatus(selectedStatus === 'EXPIRED' ? '' : 'EXPIRED'); setPage(1); }}
            >
              <div className="text-2xl font-bold text-red-600">{stats.by_status?.EXPIRED || 0}</div>
              <div className="text-sm text-gray-600">Expired</div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6">
          <div className="flex flex-wrap gap-4 items-center">
            {/* Search */}
            <div className="flex-1 min-w-[200px]">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by name, phone, or enquiry ID..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
            </div>

            {/* Batch filter */}
            <select
              value={selectedBatch}
              onChange={(e) => { setSelectedBatch(e.target.value); setPage(1); }}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Batches</option>
              {batches.map((b) => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
            </select>

            {/* Clear filters */}
            {(search || selectedStatus || selectedBatch || selectedType) && (
              <button
                onClick={() => {
                  setSearch('');
                  setSelectedStatus('');
                  setSelectedBatch('');
                  setSelectedType('');
                  setPage(1);
                }}
                className="px-3 py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Clear filters
              </button>
            )}

            <div className="text-sm text-gray-500">
              {total} student{total !== 1 ? 's' : ''}
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Student</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Age</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Parent / Phone</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Batch</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Plan</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Validity</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Classes</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Paid</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan={10} className="px-4 py-12 text-center text-gray-500">
                      <div className="flex items-center justify-center gap-2">
                        <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                        Loading students...
                      </div>
                    </td>
                  </tr>
                ) : students.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="px-4 py-12 text-center text-gray-500">
                      No students found
                    </td>
                  </tr>
                ) : (
                  students.map((s) => {
                    const primaryParent = s.parents.find((p) => p.is_primary_contact) || s.parents[0];
                    const age = calculateAge(s.child.dob || undefined, s.child.age_years || undefined);

                    return (
                      <tr
                        key={s.child.id}
                        onClick={() => handleRowClick(s)}
                        className="hover:bg-blue-50 cursor-pointer transition"
                      >
                        {/* Student */}
                        <td className="px-4 py-3">
                          <div className="font-semibold text-gray-900">
                            {s.child.first_name} {s.child.last_name || ''}
                          </div>
                          <div className="text-xs text-blue-600 font-mono">
                            {s.child.enquiry_id}
                          </div>
                        </td>

                        {/* Age */}
                        <td className="px-4 py-3 text-sm text-gray-700">
                          {age != null ? `${age}y` : '-'}
                        </td>

                        {/* Parent / Phone */}
                        <td className="px-4 py-3">
                          {primaryParent ? (
                            <>
                              <div className="text-sm text-gray-900">{primaryParent.name}</div>
                              <div className="text-xs text-gray-500">{primaryParent.phone}</div>
                            </>
                          ) : (
                            <span className="text-sm text-gray-400">-</span>
                          )}
                        </td>

                        {/* Batch */}
                        <td className="px-4 py-3">
                          {s.latest_batch ? (
                            <span className="px-2 py-1 bg-blue-50 text-blue-700 text-xs font-medium rounded">
                              {s.latest_batch.name}
                            </span>
                          ) : (
                            <span className="text-sm text-gray-400">-</span>
                          )}
                        </td>

                        {/* Plan */}
                        <td className="px-4 py-3 text-sm text-gray-700">
                          {getPlanDisplay(s.latest_plan_type)}
                        </td>

                        {/* Type (New/Renewal) */}
                        <td className="px-4 py-3">
                          {s.is_renewal ? (
                            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                              Renewal x{s.enrollment_count}
                            </span>
                          ) : (
                            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">
                              New
                            </span>
                          )}
                        </td>

                        {/* Validity */}
                        <td className="px-4 py-3 text-xs text-gray-600">
                          <div>{formatDate(s.latest_start_date)}</div>
                          <div>to {formatDate(s.latest_end_date)}</div>
                        </td>

                        {/* Classes */}
                        <td className="px-4 py-3 text-sm text-gray-700">
                          {s.latest_visits_included
                            ? `${s.latest_visits_used}/${s.latest_visits_included}`
                            : '-'}
                        </td>

                        {/* Paid */}
                        <td className="px-4 py-3 text-sm text-gray-900 text-right font-medium">
                          {s.total_paid > 0 ? `₹${s.total_paid.toLocaleString('en-IN')}` : '-'}
                        </td>

                        {/* Status */}
                        <td className="px-4 py-3 text-center">
                          <span
                            className={`px-2.5 py-1 text-xs font-medium rounded ${getStatusColor(
                              s.latest_status
                            )}`}
                          >
                            {s.latest_status}
                          </span>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 bg-gray-50">
              <div className="text-sm text-gray-600">
                Page {page} of {totalPages} ({total} students)
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(1)}
                  disabled={page === 1}
                  className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  First
                </button>
                <button
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                  className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Prev
                </button>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={page >= totalPages}
                  className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
                <button
                  onClick={() => setPage(totalPages)}
                  disabled={page >= totalPages}
                  className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Last
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Student Profile Modal */}
      {showProfile && selectedChildId && (
        <StudentProfileModal
          childId={selectedChildId}
          centerId={selectedCenter.id}
          onClose={() => {
            setShowProfile(false);
            setSelectedChildId(null);
          }}
        />
      )}
    </div>
  );
}
