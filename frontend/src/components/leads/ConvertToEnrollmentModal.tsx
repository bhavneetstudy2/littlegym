'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import DateInput from '@/components/ui/DateInput';
import { getTodayISO } from '@/lib/utils';
import { useCenterContext } from '@/hooks/useCenterContext';

interface Batch {
  id: number;
  name: string;
  age_min?: number;
  age_max?: number;
  days_of_week?: string[];
  start_time?: string;
  end_time?: string;
}

interface ConvertToEnrollmentModalProps {
  leadId: number;
  childId: number;
  childName: string;
  onClose: () => void;
  onSuccess: () => void;
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

export default function ConvertToEnrollmentModal({
  leadId,
  childId,
  childName,
  onClose,
  onSuccess,
}: ConvertToEnrollmentModalProps) {
  const { selectedCenter } = useCenterContext();

  const [batches, setBatches] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Form state
  const [batchId, setBatchId] = useState<number | ''>('');
  const [daysSelected, setDaysSelected] = useState<string[]>([]);
  const [planType, setPlanType] = useState('MONTHLY');
  const [bookedClasses, setBookedClasses] = useState('');
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState('');
  const [totalAmount, setTotalAmount] = useState('');
  const [paidAmount, setPaidAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('CASH');
  const [paymentRef, setPaymentRef] = useState('');
  const [notes, setNotes] = useState('');
  const [childAge, setChildAge] = useState('');

  useEffect(() => {
    fetchBatches();
  }, []);

  // Auto-fill days when batch is selected
  useEffect(() => {
    if (batchId) {
      const batch = batches.find(b => b.id === batchId);
      if (batch?.days_of_week) {
        setDaysSelected(batch.days_of_week);
      }
    }
  }, [batchId, batches]);

  // Auto-calculate end date and booked classes based on plan type + days per week
  useEffect(() => {
    if (startDate && planType !== 'PAY_PER_VISIT' && planType !== 'CUSTOM') {
      const start = new Date(startDate);
      let end = new Date(start);
      const daysPerWeek = Math.max(daysSelected.length, 1); // default 1 if none selected
      let weeks = 1;
      switch (planType) {
        case 'WEEKLY': weeks = 1; end.setDate(end.getDate() + 7); break;
        case 'MONTHLY': weeks = 4; end.setMonth(end.getMonth() + 1); break;
        case 'QUARTERLY': weeks = 12; end.setMonth(end.getMonth() + 3); break;
        case 'YEARLY': weeks = 48; end.setFullYear(end.getFullYear() + 1); break;
      }
      setEndDate(end.toISOString().split('T')[0]);
      // Auto-set booked classes = days_per_week × weeks
      setBookedClasses(String(daysPerWeek * weeks));
    }
  }, [startDate, planType, daysSelected.length]);

  const fetchBatches = async () => {
    try {
      const params = new URLSearchParams({ active_only: 'true' });
      if (selectedCenter?.id) {
        params.append('center_id', selectedCenter.id.toString());
      }
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

    // Validation
    if (!batchId) { setError('Please select a batch'); return; }
    if (!bookedClasses || parseInt(bookedClasses) <= 0) { setError('Booked classes is required'); return; }
    if (!totalAmount || parseFloat(totalAmount) <= 0) { setError('Total amount is required'); return; }
    if (!paidAmount) { setError('Paid amount is required'); return; }

    setLoading(true);

    try {
      const payload = {
        child_id: childId,
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
        lead_id: leadId.toString(),
        center_id: selectedCenter!.id.toString(),
      });

      await api.post(`/api/v1/enrollments?${params}`, payload);

      // Update child's age if provided
      if (childAge) {
        try {
          await api.patch(`/api/v1/enrollments/children/${childId}?center_id=${selectedCenter!.id}`, {
            age_years: parseInt(childAge),
          });
        } catch {
          // Non-critical: enrollment still created
        }
      }

      setSuccess(true);
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Failed to create enrollment');
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-green-600 text-white p-4 flex items-center justify-between rounded-t-lg">
          <div>
            <h2 className="text-lg font-bold">Convert to Enrollment</h2>
            <p className="text-green-100 text-sm">{childName}</p>
          </div>
          <button onClick={onClose} className="text-white hover:text-green-200 text-2xl" disabled={loading}>
            &times;
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-auto p-6">
          <div className="space-y-4">
            {/* Batch */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Batch <span className="text-red-500">*</span>
              </label>
              <select
                value={batchId}
                onChange={(e) => setBatchId(e.target.value ? parseInt(e.target.value) : '')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
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

            {/* Age */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Child&apos;s Age (years)
              </label>
              <input
                type="number"
                value={childAge}
                onChange={(e) => setChildAge(e.target.value)}
                placeholder="e.g. 5"
                min="0"
                max="25"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
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
                        ? 'bg-green-600 text-white border-green-600'
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
                  onChange={(e) => setPlanType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
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
                  onChange={(e) => setBookedClasses(e.target.value)}
                  placeholder="e.g. 24"
                  min="1"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Start Date + End Date */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <DateInput
                  label="Start Date"
                  value={startDate}
                  onChange={setStartDate}
                  min={getTodayISO()}
                  required
                />
              </div>
              <div>
                <DateInput
                  label="End Date"
                  value={endDate}
                  onChange={setEndDate}
                  min={startDate || getTodayISO()}
                  required
                />
              </div>
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
                  onChange={(e) => {
                    setTotalAmount(e.target.value);
                    if (!paidAmount) setPaidAmount(e.target.value);
                  }}
                  placeholder="0"
                  min="0"
                  step="0.01"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Paid Amount (₹) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  value={paidAmount}
                  onChange={(e) => setPaidAmount(e.target.value)}
                  placeholder="0"
                  min="0"
                  step="0.01"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
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
                  onChange={(e) => setPaymentMethod(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                >
                  {PAYMENT_METHODS.map(m => (
                    <option key={m.value} value={m.value}>{m.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Reference / Txn ID
                </label>
                <input
                  type="text"
                  value={paymentRef}
                  onChange={(e) => setPaymentRef(e.target.value)}
                  placeholder="Optional"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                placeholder="Optional enrollment notes..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>

            {/* Error */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            {/* Success */}
            {success && (
              <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm">
                Enrollment created successfully! Lead marked as converted.
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
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
            >
              {loading && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              )}
              {loading ? 'Enrolling...' : 'Enroll Student'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
