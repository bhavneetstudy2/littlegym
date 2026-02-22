'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { useCenter } from '@/contexts/CenterContext';
import { useCenterContext } from '@/hooks/useCenterContext';
import DateInput from '@/components/ui/DateInput';
import { getTodayISO } from '@/lib/utils';

interface ExpiringEnrollment {
  enrollment_id: number;
  child_id: number;
  batch_id: number | null;
  plan_type: string;
  status: string;
  start_date: string | null;
  end_date: string | null;
  visits_included: number | null;
  visits_used: number;
  days_selected: string[] | null;
  enquiry_id: string | null;
  child_name: string;
  age_years: number | null;
  parent_name: string | null;
  parent_phone: string | null;
  batch_name: string | null;
  days_remaining: number | null;
  visits_remaining: number | null;
  total_paid: number;
  expiry_reason: string;
}

interface Batch {
  id: number;
  name: string;
  age_min?: number;
  age_max?: number;
  days_of_week?: string[];
  start_time?: string;
  end_time?: string;
}

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

export default function RenewalsPage() {
  const { selectedCenter } = useCenter();
  const [selectedTab, setSelectedTab] = useState<7 | 14 | 30>(30);
  const [enrollments, setEnrollments] = useState<ExpiringEnrollment[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showRenewModal, setShowRenewModal] = useState(false);
  const [selectedEnrollment, setSelectedEnrollment] = useState<ExpiringEnrollment | null>(null);
  const [includeExpired, setIncludeExpired] = useState(false);

  useEffect(() => {
    fetchExpiring();
  }, [selectedTab, selectedCenter, includeExpired]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => fetchExpiring(), 400);
    return () => clearTimeout(timer);
  }, [search]);

  const fetchExpiring = async () => {
    if (!selectedCenter) return;
    try {
      setLoading(true);
      const params = new URLSearchParams({
        days: selectedTab.toString(),
        center_id: selectedCenter.id.toString(),
        visit_threshold: '5',
        include_visit_expiring: 'true',
        include_expired: includeExpired.toString(),
      });
      if (search) params.append('search', search);
      const data = await api.get<ExpiringEnrollment[]>(`/api/v1/enrollments/expiring/list?${params}`);
      setEnrollments(data);
    } catch (err) {
      console.error('Failed to fetch expiring enrollments:', err);
    } finally {
      setLoading(false);
    }
  };

  const getUrgencyBadge = (e: ExpiringEnrollment) => {
    const val = e.expiry_reason === 'visits'
      ? e.visits_remaining
      : e.days_remaining;
    if (val === null || val === undefined) return { color: 'bg-gray-100 text-gray-600', label: 'N/A' };
    if (val <= 3) return { color: 'bg-red-100 text-red-800', label: val <= 0 ? 'Overdue' : `${val} left` };
    if (val <= 7) return { color: 'bg-red-100 text-red-700', label: `${val} left` };
    if (val <= 14) return { color: 'bg-orange-100 text-orange-700', label: `${val} left` };
    return { color: 'bg-yellow-100 text-yellow-700', label: `${val} left` };
  };

  const tabs = [
    { value: 7 as const, label: 'Next 7 Days' },
    { value: 14 as const, label: 'Next 14 Days' },
    { value: 30 as const, label: 'Next 30 Days' },
  ];

  // Split into date-expiring and visit-expiring for counts
  const dateExpiring = enrollments.filter(e => e.expiry_reason === 'date' || e.expiry_reason === 'both');
  const visitExpiring = enrollments.filter(e => e.expiry_reason === 'visits' || e.expiry_reason === 'both');

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Renewals Dashboard</h1>
        <p className="text-gray-600">Track and manage expiring enrollments</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
          <div className="text-2xl font-bold text-gray-900">{loading ? '...' : enrollments.length}</div>
          <div className="text-sm text-gray-600">Total Expiring / Low Visits</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-orange-500">
          <div className="text-2xl font-bold text-gray-900">{loading ? '...' : dateExpiring.length}</div>
          <div className="text-sm text-gray-600">Date Expiring</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-purple-500">
          <div className="text-2xl font-bold text-gray-900">{loading ? '...' : visitExpiring.length}</div>
          <div className="text-sm text-gray-600">Low Visits (&le;5 remaining)</div>
        </div>
      </div>

      {/* Tabs + Search */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="flex items-center justify-between border-b border-gray-200 px-4">
          <div className="flex">
            {tabs.map(tab => (
              <button
                key={tab.value}
                onClick={() => setSelectedTab(tab.value)}
                className={`px-5 py-3 text-sm font-medium transition border-b-2 ${
                  selectedTab === tab.value
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <div className="py-2 flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={includeExpired}
                onChange={e => setIncludeExpired(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded border-gray-300"
              />
              Include Expired
            </label>
            <input
              type="text"
              placeholder="Search student, ID, parent..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm w-64 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading...</div>
        ) : enrollments.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No expiring enrollments found{search ? ` matching "${search}"` : ''}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Student</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Parent / Phone</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Batch</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Plan</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Validity</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Urgency</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Paid</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {enrollments.map(e => {
                  const urgency = getUrgencyBadge(e);
                  return (
                    <tr key={e.enrollment_id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-500 font-mono">
                        {e.enquiry_id || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{e.child_name}</div>
                        {e.age_years != null && (
                          <div className="text-xs text-gray-500">{e.age_years} yrs</div>
                        )}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{e.parent_name || '-'}</div>
                        <div className="text-xs text-gray-500">{e.parent_phone || ''}</div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {e.batch_name || '-'}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                          e.status === 'ACTIVE' ? 'bg-green-100 text-green-800' :
                          e.status === 'EXPIRED' ? 'bg-red-100 text-red-800' :
                          e.status === 'PAUSED' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {e.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {e.plan_type.replace('_', ' ')}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {e.visits_included ? (
                          <div>
                            <span className="font-medium">{e.visits_used}/{e.visits_included}</span>
                            <span className="text-gray-400 text-xs ml-1">classes</span>
                          </div>
                        ) : null}
                        {e.end_date && (
                          <div className="text-xs text-gray-500">
                            ends {new Date(e.end_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-col gap-1">
                          {e.days_remaining !== null && (
                            <span className={`px-2 py-0.5 text-xs font-semibold rounded-full inline-block w-fit ${
                              e.days_remaining <= 7 ? 'bg-red-100 text-red-800' :
                              e.days_remaining <= 14 ? 'bg-orange-100 text-orange-700' :
                              'bg-yellow-100 text-yellow-700'
                            }`}>
                              {e.days_remaining <= 0 ? 'Overdue' : `${e.days_remaining}d`}
                            </span>
                          )}
                          {e.visits_remaining !== null && (
                            <span className={`px-2 py-0.5 text-xs font-semibold rounded-full inline-block w-fit ${
                              e.visits_remaining <= 3 ? 'bg-red-100 text-red-800' :
                              'bg-purple-100 text-purple-700'
                            }`}>
                              {e.visits_remaining} visits left
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {e.total_paid > 0 ? `₹${e.total_paid.toLocaleString('en-IN')}` : '-'}
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => {
                            setSelectedEnrollment(e);
                            setShowRenewModal(true);
                          }}
                          className="px-3 py-1.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition"
                        >
                          Renew
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Renewal Modal */}
      {showRenewModal && selectedEnrollment && (
        <RenewEnrollmentModal
          enrollment={selectedEnrollment}
          onClose={() => {
            setShowRenewModal(false);
            setSelectedEnrollment(null);
          }}
          onSuccess={() => {
            setShowRenewModal(false);
            setSelectedEnrollment(null);
            fetchExpiring();
          }}
        />
      )}
    </div>
  );
}


function RenewEnrollmentModal({
  enrollment,
  onClose,
  onSuccess,
}: {
  enrollment: ExpiringEnrollment;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const { selectedCenter } = useCenterContext();

  const [batches, setBatches] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Form state - prefilled from previous enrollment
  const [batchId, setBatchId] = useState<number | ''>(enrollment.batch_id || '');
  const [daysSelected, setDaysSelected] = useState<string[]>(enrollment.days_selected || []);
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

  useEffect(() => {
    fetchBatches();
  }, []);

  // Auto-fill days when batch is changed
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
      let end = new Date(start);
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
      const params = new URLSearchParams({ active_only: 'true' });
      if (selectedCenter?.id) params.append('center_id', selectedCenter.id.toString());
      const data = await api.get<Batch[]>(`/api/v1/enrollments/batches?${params}`);
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
        child_id: enrollment.child_id,
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

      const params = new URLSearchParams({
        center_id: selectedCenter!.id.toString(),
      });

      await api.post(`/api/v1/enrollments?${params}`, payload);
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
              {enrollment.enquiry_id && <span className="font-mono mr-2">{enrollment.enquiry_id}</span>}
              {enrollment.child_name}
            </p>
          </div>
          <button onClick={onClose} className="text-white hover:text-blue-200 text-2xl" disabled={loading}>
            &times;
          </button>
        </div>

        {/* Current enrollment summary */}
        <div className="px-6 pt-4 pb-2">
          <div className="bg-gray-50 rounded-lg p-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Current Plan:</span>
              <span className="font-medium">{enrollment.plan_type.replace('_', ' ')} — {enrollment.batch_name || 'No batch'}</span>
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-gray-500">Validity:</span>
              <span>
                {enrollment.visits_included ? `${enrollment.visits_used}/${enrollment.visits_included} classes` : ''}
                {enrollment.end_date ? ` · ends ${new Date(enrollment.end_date).toLocaleDateString('en-IN')}` : ''}
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
              <label className="block text-sm font-medium text-gray-700 mb-1">Days</label>
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
              <DateInput
                label="Start Date"
                value={startDate}
                onChange={setStartDate}
                required
              />
              <DateInput
                label="End Date"
                value={endDate}
                onChange={setEndDate}
                min={startDate}
                required
              />
            </div>

            {/* Total Amount + Paid Amount */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Total Amount (₹) <span className="text-red-500">*</span>
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
                  Paid Amount (₹) <span className="text-red-500">*</span>
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
