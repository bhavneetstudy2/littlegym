'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { useCenter } from '@/contexts/CenterContext';
import type { Enrollment } from '@/types';

export default function RenewalsPage() {
  const { selectedCenter } = useCenter();
  const [selectedTab, setSelectedTab] = useState<7 | 14 | 30>(7);
  const [expiringEnrollments, setExpiringEnrollments] = useState<Enrollment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showRenewModal, setShowRenewModal] = useState(false);
  const [selectedEnrollment, setSelectedEnrollment] = useState<Enrollment | null>(null);

  useEffect(() => {
    fetchExpiringEnrollments(selectedTab);
  }, [selectedTab, selectedCenter]);

  const fetchExpiringEnrollments = async (days: number) => {
    try {
      setLoading(true);
      const data = await api.get<Enrollment[]>(
        `/api/v1/enrollments/expiring/list?days=${days}${selectedCenter ? `&center_id=${selectedCenter.id}` : ''}`
      );
      setExpiringEnrollments(data);
    } catch (err) {
      console.error('Failed to fetch expiring enrollments:', err);
    } finally {
      setLoading(false);
    }
  };

  const getDaysRemaining = (endDate: string | null): number => {
    if (!endDate) return 0;
    const today = new Date();
    const end = new Date(endDate);
    const diffTime = end.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const getUrgencyColor = (daysRemaining: number): string => {
    if (daysRemaining <= 7) return 'bg-red-100 text-red-800';
    if (daysRemaining <= 14) return 'bg-orange-100 text-orange-800';
    return 'bg-yellow-100 text-yellow-800';
  };

  const handleRenew = (enrollment: Enrollment) => {
    setSelectedEnrollment(enrollment);
    setShowRenewModal(true);
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Renewals Dashboard</h1>
        <p className="text-gray-600">Track and manage expiring enrollments</p>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setSelectedTab(7)}
            className={`flex-1 px-6 py-4 text-center font-medium transition ${
              selectedTab === 7
                ? 'border-b-2 border-blue-500 text-blue-600 bg-blue-50'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <div className="text-2xl font-bold">
              {loading && selectedTab === 7 ? '...' : expiringEnrollments.length}
            </div>
            <div className="text-sm">Expiring in 7 Days</div>
          </button>
          <button
            onClick={() => setSelectedTab(14)}
            className={`flex-1 px-6 py-4 text-center font-medium transition ${
              selectedTab === 14
                ? 'border-b-2 border-blue-500 text-blue-600 bg-blue-50'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <div className="text-2xl font-bold">
              {loading && selectedTab === 14 ? '...' : expiringEnrollments.length}
            </div>
            <div className="text-sm">Expiring in 14 Days</div>
          </button>
          <button
            onClick={() => setSelectedTab(30)}
            className={`flex-1 px-6 py-4 text-center font-medium transition ${
              selectedTab === 30
                ? 'border-b-2 border-blue-500 text-blue-600 bg-blue-50'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <div className="text-2xl font-bold">
              {loading && selectedTab === 30 ? '...' : expiringEnrollments.length}
            </div>
            <div className="text-sm">Expiring in 30 Days</div>
          </button>
        </div>
      </div>

      {/* Expiring Enrollments List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading enrollments...</div>
        ) : expiringEnrollments.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No enrollments expiring in the next {selectedTab} days
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Student Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Plan Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    End Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Days Remaining
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Visits Used
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {expiringEnrollments.map((enrollment) => {
                  const daysRemaining = getDaysRemaining(enrollment.end_date);
                  return (
                    <tr key={enrollment.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {enrollment.child?.first_name} {enrollment.child?.last_name || ''}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {enrollment.plan_type.replace('_', ' ')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {enrollment.end_date ? new Date(enrollment.end_date).toLocaleDateString() : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-semibold rounded-full ${getUrgencyColor(
                            daysRemaining
                          )}`}
                        >
                          {daysRemaining} days
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {enrollment.visits_included ? (
                          <>
                            {enrollment.visits_used} / {enrollment.visits_included}
                          </>
                        ) : (
                          'Date-based'
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => handleRenew(enrollment)}
                          className="text-blue-600 hover:text-blue-900"
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

      {/* Renew Modal */}
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
            fetchExpiringEnrollments(selectedTab);
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
  enrollment: Enrollment;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState({
    plan_type: enrollment.plan_type,
    start_date: new Date(
      (enrollment.end_date ? new Date(enrollment.end_date).getTime() : new Date().getTime()) + 24 * 60 * 60 * 1000
    )
      .toISOString()
      .split('T')[0],
    end_date: '',
    visits_included: enrollment.visits_included || 0,
    days_selected: enrollment.days_selected || [],
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      await api.post('/api/v1/enrollments', {
        child_id: enrollment.child_id,
        batch_id: enrollment.batch_id,
        plan_type: formData.plan_type,
        start_date: formData.start_date,
        end_date: formData.end_date || null,
        visits_included: formData.plan_type === 'PAY_PER_VISIT' ? formData.visits_included : null,
        days_selected: formData.days_selected,
      });
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to renew enrollment');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-md w-full p-6">
        <h2 className="text-2xl font-bold mb-4">Renew Enrollment</h2>
        <div className="mb-4 p-3 bg-blue-50 text-blue-900 rounded-lg">
          <p className="font-medium">
            {enrollment.child?.first_name} {enrollment.child?.last_name || ''}
          </p>
          <p className="text-sm">
            Current plan ends: {enrollment.end_date ? new Date(enrollment.end_date).toLocaleDateString() : 'N/A'}
          </p>
        </div>
        {error && <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Plan Type</label>
            <select
              value={formData.plan_type}
              onChange={(e) => setFormData({ ...formData, plan_type: e.target.value as any })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="PAY_PER_VISIT">Pay Per Visit</option>
              <option value="WEEKLY">Weekly</option>
              <option value="MONTHLY">Monthly</option>
              <option value="QUARTERLY">Quarterly</option>
              <option value="YEARLY">Yearly</option>
              <option value="CUSTOM">Custom</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="date"
              required
              value={formData.start_date}
              onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {formData.plan_type !== 'PAY_PER_VISIT' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Date
              </label>
              <input
                type="date"
                required
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}

          {formData.plan_type === 'PAY_PER_VISIT' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Number of Visits
              </label>
              <input
                type="number"
                required
                min="1"
                value={formData.visits_included}
                onChange={(e) =>
                  setFormData({ ...formData, visits_included: Number(e.target.value) })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}

          <div className="flex gap-3 mt-6">
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium disabled:opacity-50"
            >
              {submitting ? 'Creating...' : 'Create Renewal'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition font-medium"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
