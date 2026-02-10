'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { IntroVisit, IntroVisitUpdateData, IVOutcome, IV_OUTCOME_LABELS } from '@/types/leads';

interface UpdateIVModalProps {
  ivId: number;
  onClose: () => void;
  onSuccess: () => void;
}

export default function UpdateIVModal({ ivId, onClose, onSuccess }: UpdateIVModalProps) {
  const [introVisit, setIntroVisit] = useState<IntroVisit | null>(null);
  const [formData, setFormData] = useState<IntroVisitUpdateData>({
    attended_at: '',
    outcome: undefined,
    outcome_notes: '',
  });

  const [loading, setLoading] = useState(false);
  const [loadingIV, setLoadingIV] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    fetchIntroVisit();
  }, [ivId]);

  const fetchIntroVisit = async () => {
    setLoadingIV(true);
    try {
      const data = await api.get<IntroVisit>(`/api/v1/intro-visits/${ivId}`);
      setIntroVisit(data);

      // Pre-fill form with existing data
      setFormData({
        attended_at: data.attended_at ? new Date(data.attended_at).toISOString().slice(0, 16) : '',
        outcome: data.outcome,
        outcome_notes: data.outcome_notes || '',
      });
    } catch (err: any) {
      setError(err.message || 'Failed to load intro visit');
    } finally {
      setLoadingIV(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (formData.outcome && !formData.attended_at) {
      setError('Please provide attended date and time when setting an outcome');
      return;
    }

    setLoading(true);

    try {
      await api.patch(`/api/v1/intro-visits/${ivId}`, formData);
      setSuccess(true);
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Failed to update intro visit');
      setLoading(false);
    }
  };

  if (loadingIV) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading intro visit...</p>
        </div>
      </div>
    );
  }

  if (error && !introVisit) {
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
            <h2 className="text-xl font-bold text-gray-900">Update Intro Visit</h2>
            {introVisit && (
              <p className="text-sm text-gray-500">
                Scheduled: {formatDateTime(introVisit.scheduled_at)}
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
            {/* Attended At */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Attended Date & Time
              </label>
              <input
                type="datetime-local"
                value={formData.attended_at || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, attended_at: e.target.value }))}
                max={new Date().toISOString().slice(0, 16)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-1">
                Leave empty if child did not attend
              </p>
            </div>

            {/* Outcome */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Outcome
              </label>
              <select
                value={formData.outcome || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, outcome: e.target.value as IVOutcome || undefined }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Select Outcome</option>
                {Object.entries(IV_OUTCOME_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                What was the result of the intro visit?
              </p>
            </div>

            {/* Outcome Badge */}
            {formData.outcome && (
              <div className={`px-3 py-2 rounded-lg text-sm ${
                formData.outcome === 'INTERESTED_ENROLL_NOW' ? 'bg-green-100 text-green-800 border border-green-200' :
                formData.outcome === 'INTERESTED_ENROLL_LATER' ? 'bg-yellow-100 text-yellow-800 border border-yellow-200' :
                formData.outcome === 'NO_SHOW' ? 'bg-gray-100 text-gray-800 border border-gray-200' :
                'bg-red-100 text-red-800 border border-red-200'
              }`}>
                Selected: <strong>{IV_OUTCOME_LABELS[formData.outcome]}</strong>
              </div>
            )}

            {/* Outcome Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notes
              </label>
              <textarea
                value={formData.outcome_notes || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, outcome_notes: e.target.value }))}
                rows={4}
                placeholder="Additional notes about the intro visit, parent feedback, child's response, etc."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            {/* Success Message */}
            {success && (
              <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm">
                Intro visit updated successfully!
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
              {loading && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              )}
              {loading ? 'Updating...' : 'Update IV'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
