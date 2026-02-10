'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { FollowUp, FollowUpUpdateData, FollowUpStatus, FollowUpOutcome, FOLLOW_UP_OUTCOME_LABELS } from '@/types/leads';

interface UpdateFollowUpModalProps {
  followUpId: number;
  onClose: () => void;
  onSuccess: () => void;
}

export default function UpdateFollowUpModal({ followUpId, onClose, onSuccess }: UpdateFollowUpModalProps) {
  const [followUp, setFollowUp] = useState<FollowUp | null>(null);
  const [formData, setFormData] = useState<FollowUpUpdateData>({
    completed_at: '',
    status: undefined,
    outcome: undefined,
    notes: '',
  });

  const [loading, setLoading] = useState(false);
  const [loadingFollowUp, setLoadingFollowUp] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    fetchFollowUp();
  }, [followUpId]);

  const fetchFollowUp = async () => {
    setLoadingFollowUp(true);
    try {
      const data = await api.get<FollowUp>(`/api/v1/follow-ups/${followUpId}`);
      setFollowUp(data);

      // Pre-fill form with existing data
      setFormData({
        completed_at: data.completed_at ? new Date(data.completed_at).toISOString().slice(0, 16) : '',
        status: data.status,
        outcome: data.outcome,
        notes: data.notes || '',
      });
    } catch (err: any) {
      setError(err.message || 'Failed to load follow-up');
    } finally {
      setLoadingFollowUp(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (formData.status === 'COMPLETED' && !formData.completed_at) {
      setError('Please provide completion date and time when marking as completed');
      return;
    }
    if (formData.outcome && !formData.completed_at) {
      setError('Please provide completion date and time when setting an outcome');
      return;
    }

    setLoading(true);

    try {
      await api.patch(`/api/v1/follow-ups/${followUpId}`, formData);
      setSuccess(true);
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Failed to update follow-up');
      setLoading(false);
    }
  };

  // Auto-set completed_at when status is COMPLETED
  const handleStatusChange = (status: FollowUpStatus) => {
    setFormData(prev => {
      const newData = { ...prev, status };
      if (status === 'COMPLETED' && !prev.completed_at) {
        const now = new Date();
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
        newData.completed_at = now.toISOString().slice(0, 16);
      } else if (status !== 'COMPLETED') {
        newData.completed_at = '';
        newData.outcome = undefined;
      }
      return newData;
    });
  };

  if (loadingFollowUp) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading follow-up...</p>
        </div>
      </div>
    );
  }

  if (error && !followUp) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg p-8 max-w-md">
          <p className="text-red-500 mb-4">{error}</p>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 w-full"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="bg-white border-b p-4 flex items-center justify-between rounded-t-lg">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Update Follow-up</h2>
            {followUp && (
              <p className="text-sm text-gray-500">
                Scheduled: {formatDateTime(followUp.scheduled_date)}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
            disabled={loading}
          >
            &times;
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-4">
            {/* Status */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Status
              </label>
              <div className="flex gap-2">
                {(['PENDING', 'COMPLETED', 'CANCELLED'] as FollowUpStatus[]).map((status) => (
                  <button
                    key={status}
                    type="button"
                    onClick={() => handleStatusChange(status)}
                    className={`flex-1 px-3 py-2 text-sm rounded-lg border-2 transition-colors ${
                      formData.status === status
                        ? status === 'COMPLETED'
                          ? 'bg-green-100 border-green-500 text-green-800'
                          : status === 'CANCELLED'
                          ? 'bg-gray-100 border-gray-500 text-gray-800'
                          : 'bg-yellow-100 border-yellow-500 text-yellow-800'
                        : 'bg-white border-gray-300 text-gray-600 hover:border-gray-400'
                    }`}
                  >
                    {status}
                  </button>
                ))}
              </div>
            </div>

            {/* Completed At */}
            {formData.status === 'COMPLETED' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Completed Date & Time <span className="text-red-500">*</span>
                </label>
                <input
                  type="datetime-local"
                  value={formData.completed_at || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, completed_at: e.target.value }))}
                  max={new Date().toISOString().slice(0, 16)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  required
                />
              </div>
            )}

            {/* Outcome */}
            {formData.status === 'COMPLETED' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Outcome
                </label>
                <select
                  value={formData.outcome || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, outcome: e.target.value as FollowUpOutcome || undefined }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                >
                  <option value="">Select Outcome</option>
                  {Object.entries(FOLLOW_UP_OUTCOME_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  What was the result of this follow-up?
                </p>
              </div>
            )}

            {/* Outcome Badge */}
            {formData.outcome && (
              <div className={`px-3 py-2 rounded-lg text-sm ${
                formData.outcome === 'ENROLLED' ? 'bg-green-100 text-green-800 border border-green-200' :
                formData.outcome === 'LOST' ? 'bg-red-100 text-red-800 border border-red-200' :
                formData.outcome === 'SCHEDULED_IV' ? 'bg-blue-100 text-blue-800 border border-blue-200' :
                'bg-yellow-100 text-yellow-800 border border-yellow-200'
              }`}>
                Selected: <strong>{FOLLOW_UP_OUTCOME_LABELS[formData.outcome]}</strong>
              </div>
            )}

            {/* Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notes
              </label>
              <textarea
                value={formData.notes || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                rows={4}
                placeholder="What was discussed? What are the next steps? Any concerns or feedback?"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>

            {/* Action Hints */}
            {formData.outcome === 'ENROLLED' && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-green-800">
                <div className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p>Great! Remember to create an enrollment for this lead.</p>
                </div>
              </div>
            )}

            {formData.outcome === 'SCHEDULED_IV' && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
                <div className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <p>Remember to schedule the intro visit for this lead.</p>
                </div>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            {/* Success Message */}
            {success && (
              <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm">
                Follow-up updated successfully!
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
              {loading ? 'Updating...' : 'Update Follow-up'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
