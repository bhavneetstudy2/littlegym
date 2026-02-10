'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { IntroVisitFormData } from '@/types/leads';

interface Batch {
  id: number;
  name: string;
  age_min?: number;
  age_max?: number;
  days_of_week?: string[];
  start_time?: string;
  end_time?: string;
}

interface ScheduleIVModalProps {
  leadId: number;
  onClose: () => void;
  onSuccess: () => void;
}

export default function ScheduleIVModal({ leadId, onClose, onSuccess }: ScheduleIVModalProps) {
  const [formData, setFormData] = useState<IntroVisitFormData>({
    lead_id: leadId,
    scheduled_at: '',
    batch_id: undefined,
  });

  const [batches, setBatches] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingBatches, setLoadingBatches] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    fetchBatches();
  }, []);

  const fetchBatches = async () => {
    setLoadingBatches(true);
    try {
      const data = await api.get<Batch[]>('/api/v1/enrollments/batches');
      setBatches(data);
    } catch (err: any) {
      console.error('Failed to load batches:', err);
      setError('Failed to load batches. You can still schedule without selecting a batch.');
    } finally {
      setLoadingBatches(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!formData.scheduled_at) {
      setError('Scheduled date and time is required');
      return;
    }

    setLoading(true);

    try {
      await api.post(`/api/v1/leads/${leadId}/intro-visit`, formData);
      setSuccess(true);
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Failed to schedule intro visit');
      setLoading(false);
    }
  };

  // Get minimum datetime (now)
  const getMinDateTime = () => {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    return now.toISOString().slice(0, 16);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="bg-white border-b p-4 flex items-center justify-between rounded-t-lg">
          <h2 className="text-xl font-bold text-gray-900">Schedule Intro Visit</h2>
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
            {/* Scheduled At */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Schedule Date & Time <span className="text-red-500">*</span>
              </label>
              <input
                type="datetime-local"
                value={formData.scheduled_at}
                onChange={(e) => setFormData(prev => ({ ...prev, scheduled_at: e.target.value }))}
                min={getMinDateTime()}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Select when the intro visit should take place
              </p>
            </div>

            {/* Batch Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Batch (Optional)
              </label>
              {loadingBatches ? (
                <div className="flex items-center justify-center py-3">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                  <span className="ml-2 text-sm text-gray-500">Loading batches...</span>
                </div>
              ) : (
                <>
                  <select
                    value={formData.batch_id || ''}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      batch_id: e.target.value ? parseInt(e.target.value) : undefined
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Select a batch</option>
                    {batches.map(batch => (
                      <option key={batch.id} value={batch.id}>
                        {batch.name}
                        {batch.age_min && batch.age_max && ` (${batch.age_min}-${batch.age_max} yrs)`}
                        {batch.days_of_week && batch.days_of_week.length > 0 && ` - ${batch.days_of_week.join(', ')}`}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    Select which batch the child will attend for the intro visit
                  </p>
                </>
              )}
            </div>

            {/* Selected Batch Details */}
            {formData.batch_id && batches.find(b => b.id === formData.batch_id) && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                {(() => {
                  const selectedBatch = batches.find(b => b.id === formData.batch_id);
                  if (!selectedBatch) return null;

                  return (
                    <div className="space-y-1 text-sm">
                      <p className="font-semibold text-blue-900">{selectedBatch.name}</p>
                      {selectedBatch.age_min && selectedBatch.age_max && (
                        <p className="text-blue-700">
                          Age: {selectedBatch.age_min}-{selectedBatch.age_max} years
                        </p>
                      )}
                      {selectedBatch.days_of_week && selectedBatch.days_of_week.length > 0 && (
                        <p className="text-blue-700">
                          Days: {selectedBatch.days_of_week.join(', ')}
                        </p>
                      )}
                      {selectedBatch.start_time && selectedBatch.end_time && (
                        <p className="text-blue-700">
                          Time: {selectedBatch.start_time} - {selectedBatch.end_time}
                        </p>
                      )}
                    </div>
                  );
                })()}
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
                Intro visit scheduled successfully!
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
              {loading ? 'Scheduling...' : 'Schedule IV'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
