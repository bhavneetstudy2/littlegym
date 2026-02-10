'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { LeadCloseData } from '@/types/leads';

interface CloseLeadModalProps {
  leadId: number;
  onClose: () => void;
  onSuccess: () => void;
}

const COMMON_REASONS = [
  'Not interested in the program',
  'Cost/pricing concerns',
  'Timing/schedule conflicts',
  'Location too far',
  'Joined another gym/activity',
  'Child not ready/too young',
  'Parent not responsive',
  'Moved to different city',
  'Other',
];

export default function CloseLeadModal({ leadId, onClose, onSuccess }: CloseLeadModalProps) {
  const [formData, setFormData] = useState<LeadCloseData>({
    reason: '',
  });

  const [selectedCommonReason, setSelectedCommonReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleCommonReasonSelect = (reason: string) => {
    setSelectedCommonReason(reason);
    if (reason === 'Other') {
      setFormData({ reason: '' });
    } else {
      setFormData({ reason });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!formData.reason || formData.reason.trim().length < 5) {
      setError('Please provide a reason (at least 5 characters)');
      return;
    }

    setLoading(true);

    try {
      await api.post(`/api/v1/leads/${leadId}/close`, formData);
      setSuccess(true);
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Failed to close lead');
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="bg-red-50 border-b border-red-200 p-4 flex items-center justify-between rounded-t-lg">
          <div className="flex items-center gap-2">
            <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <h2 className="text-xl font-bold text-red-900">Close Lead</h2>
          </div>
          <button
            onClick={onClose}
            className="text-red-400 hover:text-red-600 text-2xl"
            disabled={loading}
          >
            &times;
          </button>
        </div>

        {/* Warning Message */}
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 m-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                This will mark the lead as <strong>Lost</strong> and move it out of the active pipeline.
              </p>
            </div>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-4">
            {/* Common Reasons */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select a Reason
              </label>
              <div className="space-y-2">
                {COMMON_REASONS.map((reason) => (
                  <label
                    key={reason}
                    className={`flex items-center gap-2 p-3 rounded-lg border-2 cursor-pointer transition-colors ${
                      selectedCommonReason === reason
                        ? 'border-red-500 bg-red-50'
                        : 'border-gray-200 hover:border-gray-300 bg-white'
                    }`}
                  >
                    <input
                      type="radio"
                      name="commonReason"
                      value={reason}
                      checked={selectedCommonReason === reason}
                      onChange={(e) => handleCommonReasonSelect(e.target.value)}
                      className="w-4 h-4 text-red-600 border-gray-300 focus:ring-red-500"
                    />
                    <span className="text-sm text-gray-700">{reason}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Custom Reason */}
            {(selectedCommonReason === 'Other' || !selectedCommonReason) && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Reason Details <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={formData.reason}
                  onChange={(e) => setFormData({ reason: e.target.value })}
                  rows={4}
                  placeholder="Please provide detailed reason for closing this lead..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  required
                  minLength={5}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Minimum 5 characters required. This helps track why leads don't convert.
                </p>
              </div>
            )}

            {/* Additional Notes for pre-selected reasons */}
            {selectedCommonReason && selectedCommonReason !== 'Other' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Additional Details (Optional)
                </label>
                <textarea
                  value={formData.reason}
                  onChange={(e) => setFormData({ reason: e.target.value })}
                  rows={3}
                  placeholder="Any additional details about the closure reason..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                />
              </div>
            )}

            {/* Info Box */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
              <div className="flex items-start gap-2">
                <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <p className="font-medium mb-1">Good to know:</p>
                  <ul className="text-xs space-y-0.5">
                    <li>Lead data will be preserved for future reference</li>
                    <li>You can reopen a lead later if needed</li>
                    <li>This helps analyze conversion patterns</li>
                  </ul>
                </div>
              </div>
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
                Lead closed successfully!
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
              disabled={loading || success || (!formData.reason || formData.reason.trim().length < 5)}
              className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
            >
              {loading && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              )}
              {loading ? 'Closing...' : 'Close Lead'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
