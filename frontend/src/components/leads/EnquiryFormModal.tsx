'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { EnquiryFormData, LeadSource, PARENT_EXPECTATIONS } from '@/types/leads';

interface EnquiryFormModalProps {
  onClose: () => void;
  onSuccess: () => void;
  centerId: number;
}

const SOURCES: { value: LeadSource; label: string }[] = [
  { value: 'WALK_IN', label: 'Walk-in' },
  { value: 'PHONE_CALL', label: 'Phone Call' },
  { value: 'ONLINE', label: 'Online' },
  { value: 'REFERRAL', label: 'Referral' },
  { value: 'INSTAGRAM', label: 'Instagram' },
  { value: 'FACEBOOK', label: 'Facebook' },
  { value: 'GOOGLE', label: 'Google' },
  { value: 'OTHER', label: 'Other' },
];

const EXPECTATION_LABELS: Record<string, string> = {
  child_development: 'Child Development',
  physical_activity: 'Physical Activity',
  socialization_skills: 'Socialization Skills',
  confidence_building: 'Confidence Building',
  motor_skills: 'Motor Skills',
  fun_recreation: 'Fun & Recreation',
  structured_program: 'Structured Program',
  experienced_trainers: 'Experienced Trainers',
};

export default function EnquiryFormModal({ onClose, onSuccess, centerId }: EnquiryFormModalProps) {
  const [formData, setFormData] = useState<EnquiryFormData>({
    child_first_name: '',
    child_last_name: '',
    child_dob: '',
    age: undefined,
    gender: undefined,
    parent_name: '',
    contact_number: '',
    email: '',
    school: '',
    source: undefined,
    parent_expectations: [],
    preferred_schedule: '',
    remarks: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Auto-calculate age from DOB
  const handleDobChange = (dob: string) => {
    setFormData(prev => {
      const newData = { ...prev, child_dob: dob };
      if (dob) {
        const today = new Date();
        const birthDate = new Date(dob);
        let age = today.getFullYear() - birthDate.getFullYear();
        const m = today.getMonth() - birthDate.getMonth();
        if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
          age--;
        }
        newData.age = age;
      } else {
        newData.age = undefined;
      }
      return newData;
    });
  };

  // Toggle expectation checkbox
  const toggleExpectation = (expectation: string) => {
    setFormData(prev => {
      const current = prev.parent_expectations || [];
      const newExpectations = current.includes(expectation)
        ? current.filter(e => e !== expectation)
        : [...current, expectation];
      return { ...prev, parent_expectations: newExpectations };
    });
  };

  // Validate phone number
  const validatePhone = (phone: string): boolean => {
    const phoneRegex = /^[6-9]\d{9}$/;
    return phoneRegex.test(phone);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!formData.child_first_name.trim()) {
      setError('Child first name is required');
      return;
    }
    if (!formData.parent_name.trim()) {
      setError('Parent name is required');
      return;
    }
    if (!formData.contact_number.trim()) {
      setError('Contact number is required');
      return;
    }
    if (!validatePhone(formData.contact_number)) {
      setError('Please enter a valid 10-digit Indian mobile number');
      return;
    }

    setLoading(true);

    try {
      // Clean form data: convert empty strings to null for optional fields
      const cleanedData = {
        center_id: centerId,
        child_first_name: formData.child_first_name,
        child_last_name: formData.child_last_name || null,
        child_dob: formData.child_dob || null,
        age: formData.age || null,
        gender: formData.gender || null,
        parent_name: formData.parent_name,
        contact_number: formData.contact_number,
        email: formData.email || null,
        school: formData.school || null,
        source: formData.source || null,
        parent_expectations: formData.parent_expectations && formData.parent_expectations.length > 0
          ? formData.parent_expectations
          : null,
        preferred_schedule: formData.preferred_schedule || null,
        remarks: formData.remarks || null,
      };

      await api.post('/api/v1/leads/enquiry', cleanedData);
      setSuccess(true);
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Failed to submit enquiry');
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-white border-b p-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">New Enquiry</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
            disabled={loading}
          >
            &times;
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-auto p-6">
          <div className="space-y-6">
            {/* Child Information */}
            <div className="bg-blue-50 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Child Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    First Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.child_first_name}
                    onChange={(e) => setFormData(prev => ({ ...prev, child_first_name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Last Name
                  </label>
                  <input
                    type="text"
                    value={formData.child_last_name || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, child_last_name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    value={formData.child_dob || ''}
                    onChange={(e) => handleDobChange(e.target.value)}
                    max={new Date().toISOString().split('T')[0]}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Age
                  </label>
                  <input
                    type="number"
                    value={formData.age || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, age: e.target.value ? parseInt(e.target.value) : undefined }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-50"
                    readOnly={!!formData.child_dob}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Gender
                  </label>
                  <select
                    value={formData.gender || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, gender: e.target.value as any }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Select Gender</option>
                    <option value="Boy">Boy</option>
                    <option value="Girl">Girl</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    School
                  </label>
                  <input
                    type="text"
                    value={formData.school || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, school: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>

            {/* Parent Information */}
            <div className="bg-green-50 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Parent Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Parent Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.parent_name}
                    onChange={(e) => setFormData(prev => ({ ...prev, parent_name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Contact Number <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="tel"
                    value={formData.contact_number}
                    onChange={(e) => setFormData(prev => ({ ...prev, contact_number: e.target.value.replace(/\D/g, '').slice(0, 10) }))}
                    pattern="[6-9]\d{9}"
                    placeholder="10-digit mobile number"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    required
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    value={formData.email || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>

            {/* Discovery Information */}
            <div className="bg-purple-50 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Discovery Information</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Source
                  </label>
                  <select
                    value={formData.source || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, source: e.target.value as LeadSource }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    <option value="">Select Source</option>
                    {SOURCES.map(source => (
                      <option key={source.value} value={source.value}>
                        {source.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Parent Expectations
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {PARENT_EXPECTATIONS.map(expectation => (
                      <label key={expectation} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.parent_expectations?.includes(expectation) || false}
                          onChange={() => toggleExpectation(expectation)}
                          className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                        />
                        <span className="text-sm text-gray-700">
                          {EXPECTATION_LABELS[expectation] || expectation}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Preferred Schedule
                  </label>
                  <textarea
                    value={formData.preferred_schedule || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, preferred_schedule: e.target.value }))}
                    rows={2}
                    placeholder="e.g., Weekends, Evenings after 5 PM"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Remarks / Additional Notes
                  </label>
                  <textarea
                    value={formData.remarks || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, remarks: e.target.value }))}
                    rows={3}
                    placeholder="Any additional information or special requirements"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            {/* Success Message */}
            {success && (
              <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
                Enquiry submitted successfully!
              </div>
            )}
          </div>
        </form>

        {/* Footer */}
        <div className="bg-gray-50 border-t p-4 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || success}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
          >
            {loading && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            )}
            {loading ? 'Submitting...' : 'Submit Enquiry'}
          </button>
        </div>
      </div>
    </div>
  );
}
