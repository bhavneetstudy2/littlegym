'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useCenter } from '@/contexts/CenterContext';
import { api } from '@/lib/api';
import StudentProfileModal from '@/components/StudentProfileModal';

interface Batch {
  id: number;
  name: string;
  age_min: number;
  age_max: number;
  days_of_week?: string[];
  start_time?: string;
  end_time?: string;
  active: boolean;
}

interface Child {
  id: number;
  enquiry_id?: string;
  first_name: string;
  last_name?: string;
  dob?: string;
  school?: string;
}

interface Parent {
  id: number;
  name: string;
  phone: string;
  email?: string;
}

interface Enrollment {
  id: number;
  plan_type: string;
  status: string;
  start_date?: string;
  end_date?: string;
  visits_included?: number;
  visits_used: number;
  days_selected?: string[];
  child?: Child;
  batch?: Batch;
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
  child: Child;
  parents: Parent[];
  batch?: Batch;
  total_paid: number;
}

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

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    ACTIVE: 'bg-green-100 text-green-800',
    EXPIRED: 'bg-red-100 text-red-800',
    CANCELLED: 'bg-gray-100 text-gray-800',
    PAUSED: 'bg-yellow-100 text-yellow-800',
  };
  return colors[status] || 'bg-gray-100 text-gray-800';
};

const formatDate = (dateString?: string) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  });
};

export default function EnrollmentsPage() {
  const router = useRouter();
  const { selectedCenter } = useCenter();
  const [enrollments, setEnrollments] = useState<EnrolledStudent[]>([]);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [batchCounts, setBatchCounts] = useState<Record<number, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('ACTIVE');
  const [batchFilter, setBatchFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(null);
  const [selectedEnrollmentId, setSelectedEnrollmentId] = useState<number | null>(null);
  const [sortField, setSortField] = useState<string>('');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Debounce the search query (400ms)
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchQuery), 400);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Re-fetch when center, status, batch, or debounced search changes
  useEffect(() => {
    if (selectedCenter) {
      fetchData();
    }
  }, [selectedCenter, statusFilter, batchFilter, debouncedSearch]);

  const fetchData = async () => {
    if (!selectedCenter) return;

    setLoading(true);
    setError(null);

    try {
      let url = `/api/v1/enrollments/students?center_id=${selectedCenter.id}&limit=200`;
      if (statusFilter) url += `&status=${statusFilter}`;
      if (batchFilter) url += `&batch_id=${batchFilter}`;
      if (debouncedSearch.trim().length >= 2) url += `&search=${encodeURIComponent(debouncedSearch.trim())}`;

      // Always fetch counts without batch filter so batch cards show accurate totals
      let countUrl = `/api/v1/enrollments/students?center_id=${selectedCenter.id}&limit=500`;
      if (statusFilter) countUrl += `&status=${statusFilter}`;
      if (debouncedSearch.trim().length >= 2) countUrl += `&search=${encodeURIComponent(debouncedSearch.trim())}`;

      const [enrollmentsRes, batchesRes, allForCounts] = await Promise.all([
        api.get<EnrolledStudent[]>(url),
        api.get<Batch[]>(`/api/v1/enrollments/batches?center_id=${selectedCenter.id}`),
        batchFilter ? api.get<EnrolledStudent[]>(countUrl) : Promise.resolve(null),
      ]);

      setEnrollments(enrollmentsRes);
      setBatches(batchesRes);

      // Compute batch counts from unfiltered data
      const countsSource = allForCounts || enrollmentsRes;
      const counts: Record<number, number> = {};
      countsSource.forEach(e => {
        if (e.batch?.id) {
          counts[e.batch.id] = (counts[e.batch.id] || 0) + 1;
        }
      });
      setBatchCounts(counts);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load enrollments');
    } finally {
      setLoading(false);
    }
  };

  const filteredEnrollments = [...enrollments].sort((a, b) => {
    if (!sortField) return 0;
    const dir = sortDirection === 'asc' ? 1 : -1;
    switch (sortField) {
      case 'student':
        return dir * (a.child.first_name || '').localeCompare(b.child.first_name || '');
      case 'batch':
        return dir * (a.batch?.name || '').localeCompare(b.batch?.name || '');
      case 'plan':
        return dir * a.plan_type.localeCompare(b.plan_type);
      case 'validity':
        return dir * ((a.start_date || '') > (b.start_date || '') ? 1 : -1);
      case 'visits':
        return dir * (a.visits_used - b.visits_used);
      case 'paid':
        return dir * (a.total_paid - b.total_paid);
      case 'status':
        return dir * a.status.localeCompare(b.status);
      default:
        return 0;
    }
  });

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
                <h1 className="text-xl font-bold text-gray-900">Enrollments</h1>
                <p className="text-sm text-gray-500">{selectedCenter.name} - {filteredEnrollments.length} enrollments</p>
              </div>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium"
            >
              + New Enrollment
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Batch Overview Cards */}
        {batches.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
            {batches.map((batch) => {
              const batchCount = batchCounts[batch.id] || 0;
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

        {/* Filters */}
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

        {/* Enrollments Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-gray-500">Loading enrollments...</div>
          ) : error ? (
            <div className="p-8 text-center text-red-500">Error: {error}</div>
          ) : filteredEnrollments.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              No enrollments found. Create your first enrollment!
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">#</th>
                    {[
                      { key: 'student', label: 'Student' },
                      { key: '', label: 'Parent' },
                      { key: 'batch', label: 'Batch' },
                      { key: 'plan', label: 'Plan' },
                      { key: 'validity', label: 'Validity' },
                      { key: 'visits', label: 'Visits' },
                      { key: 'paid', label: 'Paid' },
                      { key: 'status', label: 'Status' },
                    ].map(col => (
                      <th
                        key={col.label}
                        className={`px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase ${col.key ? 'cursor-pointer hover:text-gray-700 select-none' : ''} ${col.label === 'Status' ? 'text-center' : ''}`}
                        onClick={() => col.key && handleSort(col.key)}
                      >
                        <span className="inline-flex items-center gap-1">
                          {col.label}
                          {col.key && sortField === col.key && (
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={sortDirection === 'asc' ? 'M5 15l7-7 7 7' : 'M19 9l-7 7-7-7'} />
                            </svg>
                          )}
                        </span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredEnrollments.map((enrollment, idx) => {
                    const primaryParent = enrollment.parents.find(p => p) || enrollment.parents[0];
                    return (
                      <tr
                        key={enrollment.enrollment_id}
                        className="hover:bg-gray-50 cursor-pointer"
                        onClick={() => { setSelectedStudentId(enrollment.child.id); setSelectedEnrollmentId(enrollment.enrollment_id); }}
                      >
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{idx + 1}</td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="text-sm font-medium text-blue-600">
                            {enrollment.child.first_name} {enrollment.child.last_name || ''}
                          </div>
                          {enrollment.child.enquiry_id && (
                            <div className="text-xs text-blue-500">{enrollment.child.enquiry_id}</div>
                          )}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm">
                          {primaryParent ? (
                            <div>
                              <div className="text-gray-900">{primaryParent.name}</div>
                              <div className="text-blue-600">{primaryParent.phone}</div>
                            </div>
                          ) : '-'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          {enrollment.batch ? (
                            <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs">
                              {enrollment.batch.name}
                            </span>
                          ) : '-'}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs">
                            {getPlanDisplay(enrollment.plan_type)}
                          </span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(enrollment.start_date)} - {formatDate(enrollment.end_date)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm">
                          <span className="font-medium">{enrollment.visits_used}</span>
                          <span className="text-gray-400">/{enrollment.visits_included || '?'}</span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className="font-medium text-green-600">Rs.{enrollment.total_paid.toLocaleString()}</span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-center">
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(enrollment.status)}`}>
                            {enrollment.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Create Enrollment Modal */}
      {showCreateModal && (
        <CreateEnrollmentModal
          centerId={selectedCenter.id}
          batches={batches}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            fetchData();
          }}
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

function CreateEnrollmentModal({
  centerId,
  batches,
  onClose,
  onSuccess
}: {
  centerId: number;
  batches: Batch[];
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [step, setStep] = useState<'child' | 'enrollment'>('child');
  const [childData, setChildData] = useState({
    first_name: '',
    last_name: '',
    dob: '',
    school: '',
    age_years: ''
  });
  const [parentData, setParentData] = useState({
    name: '',
    phone: '',
    email: ''
  });
  const [showSecondParent, setShowSecondParent] = useState(false);
  const [parent2Data, setParent2Data] = useState({
    name: '',
    phone: '',
    email: '',
    relationship_type: ''
  });
  const [enrollmentData, setEnrollmentData] = useState({
    batch_id: '',
    plan_type: 'MONTHLY',
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
    visits_included: '',
    days_selected: [] as string[],
    payment_amount: '',
    payment_method: 'CASH',
    payment_reference: '',
    notes: ''
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const PLAN_TYPES = ['PAY_PER_VISIT', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY', 'CUSTOM'];
  const PAYMENT_METHODS = ['CASH', 'UPI', 'CARD', 'BANK_TRANSFER', 'OTHER'];

  const toggleDay = (day: string) => {
    setEnrollmentData(prev => ({
      ...prev,
      days_selected: prev.days_selected.includes(day)
        ? prev.days_selected.filter(d => d !== day)
        : [...prev.days_selected, day]
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    if (!enrollmentData.batch_id) {
      setError('Please select a batch');
      setSubmitting(false);
      return;
    }

    if (!enrollmentData.payment_amount || parseFloat(enrollmentData.payment_amount) <= 0) {
      setError('Please enter a valid payment amount');
      setSubmitting(false);
      return;
    }

    try {
      // First create a lead (which creates child + parent)
      const parentsPayload = [{
        name: parentData.name,
        phone: parentData.phone,
        email: parentData.email || null
      }];
      if (showSecondParent && parent2Data.name && parent2Data.phone) {
        parentsPayload.push({
          name: parent2Data.name,
          phone: parent2Data.phone,
          email: parent2Data.email || null
        });
      }
      const leadRes = await api.post<{ id: number; child_id: number }>('/api/v1/leads', {
        child_first_name: childData.first_name,
        child_last_name: childData.last_name || null,
        child_dob: childData.dob || null,
        child_school: childData.school || null,
        child_age_years: childData.age_years ? parseInt(childData.age_years) : null,
        parents: parentsPayload,
        source: 'WALK_IN',
        center_id: centerId
      });

      // Create enrollment
      await api.post(`/api/v1/enrollments?lead_id=${leadRes.id}&center_id=${centerId}`, {
        child_id: leadRes.child_id,
        batch_id: parseInt(enrollmentData.batch_id),
        plan_type: enrollmentData.plan_type,
        start_date: enrollmentData.start_date,
        end_date: enrollmentData.end_date || null,
        visits_included: enrollmentData.visits_included ? parseInt(enrollmentData.visits_included) : null,
        days_selected: enrollmentData.days_selected.length > 0 ? enrollmentData.days_selected : null,
        notes: enrollmentData.notes || null,
        payment: {
          amount: parseFloat(enrollmentData.payment_amount),
          method: enrollmentData.payment_method,
          reference: enrollmentData.payment_reference || null,
          paid_at: new Date().toISOString()
        }
      });

      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to create enrollment');
    } finally {
      setSubmitting(false);
    }
  };

  const activeBatches = batches.filter(b => b.active);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">New Enrollment</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">{error}</div>
          )}

          {/* Step Tabs */}
          <div className="flex mb-6 border-b">
            <button
              onClick={() => setStep('child')}
              className={`px-4 py-2 font-medium ${
                step === 'child'
                  ? 'text-green-600 border-b-2 border-green-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              1. Child & Parent
            </button>
            <button
              onClick={() => setStep('enrollment')}
              disabled={!childData.first_name || !parentData.name || !parentData.phone}
              className={`px-4 py-2 font-medium ${
                step === 'enrollment'
                  ? 'text-green-600 border-b-2 border-green-600'
                  : 'text-gray-500 hover:text-gray-700 disabled:text-gray-300'
              }`}
            >
              2. Enrollment & Payment
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            {step === 'child' && (
              <div className="space-y-6">
                {/* Child Information */}
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="font-semibold mb-3 text-blue-800">Child Information</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">First Name *</label>
                      <input
                        type="text"
                        required
                        value={childData.first_name}
                        onChange={(e) => setChildData({ ...childData, first_name: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                      <input
                        type="text"
                        value={childData.last_name}
                        onChange={(e) => setChildData({ ...childData, last_name: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Date of Birth</label>
                      <input
                        type="date"
                        value={childData.dob}
                        onChange={(e) => setChildData({ ...childData, dob: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">School</label>
                      <input
                        type="text"
                        value={childData.school}
                        onChange={(e) => setChildData({ ...childData, school: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Age (years)</label>
                      <input
                        type="number"
                        value={childData.age_years}
                        onChange={(e) => setChildData({ ...childData, age_years: e.target.value })}
                        placeholder="e.g. 5"
                        min="0"
                        max="25"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                  </div>
                </div>

                {/* Parent Information */}
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="font-semibold mb-3 text-green-800">Parent/Guardian Information</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                      <input
                        type="text"
                        required
                        value={parentData.name}
                        onChange={(e) => setParentData({ ...parentData, name: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Phone *</label>
                      <input
                        type="tel"
                        required
                        value={parentData.phone}
                        onChange={(e) => setParentData({ ...parentData, phone: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                      <input
                        type="email"
                        value={parentData.email}
                        onChange={(e) => setParentData({ ...parentData, email: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                  </div>

                  {/* Second Parent Toggle */}
                  {!showSecondParent ? (
                    <button
                      type="button"
                      onClick={() => setShowSecondParent(true)}
                      className="mt-3 text-sm text-green-600 hover:text-green-800 font-medium flex items-center gap-1"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      Add Second Parent/Guardian
                    </button>
                  ) : (
                    <div className="mt-3 pt-3 border-t border-green-200">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-sm font-medium text-green-700">Second Parent/Guardian</h4>
                        <button
                          type="button"
                          onClick={() => { setShowSecondParent(false); setParent2Data({ name: '', phone: '', email: '', relationship_type: '' }); }}
                          className="text-xs text-red-500 hover:text-red-700"
                        >
                          Remove
                        </button>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                          <input
                            type="text"
                            value={parent2Data.name}
                            onChange={(e) => setParent2Data({ ...parent2Data, name: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                          <input
                            type="tel"
                            value={parent2Data.phone}
                            onChange={(e) => setParent2Data({ ...parent2Data, phone: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                          <input
                            type="email"
                            value={parent2Data.email}
                            onChange={(e) => setParent2Data({ ...parent2Data, email: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Relationship</label>
                          <select
                            value={parent2Data.relationship_type}
                            onChange={(e) => setParent2Data({ ...parent2Data, relationship_type: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                          >
                            <option value="">Select</option>
                            <option value="mother">Mother</option>
                            <option value="father">Father</option>
                            <option value="guardian">Guardian</option>
                            <option value="other">Other</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={() => setStep('enrollment')}
                    disabled={!childData.first_name || !parentData.name || !parentData.phone}
                    className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                  >
                    Next: Enrollment Details
                  </button>
                </div>
              </div>
            )}

            {step === 'enrollment' && (
              <div className="space-y-6">
                {/* Batch Selection */}
                <div className="bg-orange-50 p-4 rounded-lg">
                  <h3 className="font-semibold mb-3 text-orange-800">Batch Selection *</h3>
                  <select
                    value={enrollmentData.batch_id}
                    onChange={(e) => setEnrollmentData({ ...enrollmentData, batch_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    required
                  >
                    <option value="">Select a batch</option>
                    {activeBatches.map(b => (
                      <option key={b.id} value={b.id}>
                        {b.name} ({b.age_min}-{b.age_max}y) {b.days_of_week?.join(', ')}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Plan Details */}
                <div className="bg-purple-50 p-4 rounded-lg">
                  <h3 className="font-semibold mb-3 text-purple-800">Plan Details</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Plan Type *</label>
                      <select
                        value={enrollmentData.plan_type}
                        onChange={(e) => setEnrollmentData({ ...enrollmentData, plan_type: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      >
                        {PLAN_TYPES.map(type => (
                          <option key={type} value={type}>{type.replace('_', ' ')}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Start Date *</label>
                      <input
                        type="date"
                        required
                        value={enrollmentData.start_date}
                        onChange={(e) => setEnrollmentData({ ...enrollmentData, start_date: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                      <input
                        type="date"
                        value={enrollmentData.end_date}
                        onChange={(e) => setEnrollmentData({ ...enrollmentData, end_date: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                    {enrollmentData.plan_type === 'PAY_PER_VISIT' && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Visits Included</label>
                        <input
                          type="number"
                          value={enrollmentData.visits_included}
                          onChange={(e) => setEnrollmentData({ ...enrollmentData, visits_included: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                          placeholder="e.g., 12"
                        />
                      </div>
                    )}
                  </div>

                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Days Selected</label>
                    <div className="flex flex-wrap gap-2">
                      {DAYS.map(day => (
                        <button
                          key={day}
                          type="button"
                          onClick={() => toggleDay(day)}
                          className={`px-3 py-1.5 text-sm rounded-lg border ${
                            enrollmentData.days_selected.includes(day)
                              ? 'bg-purple-600 text-white border-purple-600'
                              : 'bg-white text-gray-700 border-gray-300 hover:border-purple-400'
                          }`}
                        >
                          {day}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Payment Details */}
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <h3 className="font-semibold mb-3 text-yellow-800">Payment Details *</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Amount (INR) *</label>
                      <input
                        type="number"
                        required
                        value={enrollmentData.payment_amount}
                        onChange={(e) => setEnrollmentData({ ...enrollmentData, payment_amount: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                        placeholder="e.g., 5000"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Payment Method *</label>
                      <select
                        value={enrollmentData.payment_method}
                        onChange={(e) => setEnrollmentData({ ...enrollmentData, payment_method: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      >
                        {PAYMENT_METHODS.map(method => (
                          <option key={method} value={method}>{method.replace('_', ' ')}</option>
                        ))}
                      </select>
                    </div>
                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Reference/Transaction ID</label>
                      <input
                        type="text"
                        value={enrollmentData.payment_reference}
                        onChange={(e) => setEnrollmentData({ ...enrollmentData, payment_reference: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                        placeholder="UPI ID / Transaction number"
                      />
                    </div>
                  </div>
                </div>

                {/* Notes */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                  <textarea
                    value={enrollmentData.notes}
                    rows={2}
                    onChange={(e) => setEnrollmentData({ ...enrollmentData, notes: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    placeholder="Any additional notes..."
                  />
                </div>

                <div className="flex gap-3 pt-4 border-t">
                  <button
                    type="button"
                    onClick={() => setStep('child')}
                    className="px-4 py-3 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 font-medium"
                  >
                    Back
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="flex-1 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium"
                  >
                    {submitting ? 'Creating...' : 'Complete Enrollment'}
                  </button>
                </div>
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}
