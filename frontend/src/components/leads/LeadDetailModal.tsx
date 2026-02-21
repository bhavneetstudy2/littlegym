'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import type { Lead, LeadDetail, IntroVisit, FollowUp, Parent } from '@/types/leads';
import { STATUS_CONFIGS, IV_OUTCOME_LABELS, FOLLOW_UP_OUTCOME_LABELS } from '@/types/leads';
import EditChildModal from './EditChildModal';
import EditParentModal from './EditParentModal';

interface LeadActivity {
  id: number;
  lead_id: number;
  activity_type: string;
  description: string;
  old_value?: string;
  new_value?: string;
  performed_by_id: number;
  performed_by_name?: string;
  performed_at: string;
  created_at: string;
}

interface LeadDetailModalProps {
  lead: Lead;
  detail: LeadDetail;
  onClose: () => void;
  onScheduleIV?: () => void;
  onUpdateIV?: (iv: IntroVisit) => void;
  onCreateFollowUp?: () => void;
  onUpdateFollowUp?: (followUp: FollowUp) => void;
  onCloseLead?: () => void;
  onRefresh?: () => void;
}

const formatDate = (dateString?: string) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  });
};

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

const calculateAge = (dob?: string) => {
  if (!dob) return null;
  const today = new Date();
  const birthDate = new Date(dob);
  let age = today.getFullYear() - birthDate.getFullYear();
  const m = today.getMonth() - birthDate.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }
  return age;
};

const ACTIVITY_TYPE_COLORS: Record<string, string> = {
  LEAD_CREATED: 'bg-blue-100 text-blue-700',
  STATUS_CHANGED: 'bg-yellow-100 text-yellow-700',
  IV_SCHEDULED: 'bg-purple-100 text-purple-700',
  IV_UPDATED: 'bg-purple-100 text-purple-700',
  FOLLOW_UP_CREATED: 'bg-orange-100 text-orange-700',
  FOLLOW_UP_UPDATED: 'bg-orange-100 text-orange-700',
  DISCOVERY_COMPLETED: 'bg-indigo-100 text-indigo-700',
  LEAD_CONVERTED: 'bg-green-100 text-green-700',
  LEAD_CLOSED: 'bg-red-100 text-red-700',
};

export default function LeadDetailModal({
  lead: leadProp,
  detail,
  onClose,
  onScheduleIV,
  onUpdateIV,
  onCreateFollowUp,
  onUpdateFollowUp,
  onCloseLead,
  onRefresh,
}: LeadDetailModalProps) {
  const [activities, setActivities] = useState<LeadActivity[]>([]);
  const [loadingActivities, setLoadingActivities] = useState(true);
  const [activeTab, setActiveTab] = useState<'details' | 'timeline'>('details');
  const [showEditChildModal, setShowEditChildModal] = useState(false);
  const [showEditParentModal, setShowEditParentModal] = useState(false);
  const [selectedParent, setSelectedParent] = useState<Parent | null>(null);

  const lead = detail;
  const statusConfig = STATUS_CONFIGS[lead.status];
  const child = lead.child;
  const age = child?.age || calculateAge(child?.dob);
  const primaryParent = lead.parents?.find(p => p.is_primary) || lead.parents?.[0];

  useEffect(() => {
    fetchActivities();
  }, [leadProp.id]);

  const fetchActivities = async () => {
    setLoadingActivities(true);
    try {
      const data = await api.get<LeadActivity[]>(`/api/v1/leads/${leadProp.id}/activities`);
      setActivities(data);
    } catch {
      setActivities([]);
    } finally {
      setLoadingActivities(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-white border-b p-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                {child?.enquiry_id && <span className="text-blue-600 mr-2">{child.enquiry_id}</span>}
                {child?.first_name} {child?.last_name || ''}
              </h2>
              <p className="text-sm text-gray-500">
                {age ? `${age} years` : ''}
                {primaryParent ? ` | ${primaryParent.name} (${primaryParent.phone})` : ''}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusConfig?.color || 'bg-gray-100'}`}>
                {statusConfig?.label || lead.status}
              </span>
              <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl ml-2">
                &times;
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-4 mt-4">
            <button
              onClick={() => setActiveTab('details')}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg transition ${
                activeTab === 'details'
                  ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Details
            </button>
            <button
              onClick={() => setActiveTab('timeline')}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg transition ${
                activeTab === 'timeline'
                  ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Activity Timeline ({activities.length})
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6 bg-gray-50">
          {activeTab === 'details' ? (
            <div className="space-y-6">
              {/* Child Information */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-4 border-b pb-2">
                  <h3 className="text-lg font-semibold text-gray-900">Child Information</h3>
                  <button
                    onClick={() => setShowEditChildModal(true)}
                    className="text-sm px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition"
                  >
                    Edit
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-gray-500 text-sm">Enquiry ID</span>
                    <p className="font-medium text-blue-600">{child?.enquiry_id || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-gray-500 text-sm">Name</span>
                    <p className="font-medium">{child?.first_name} {child?.last_name || ''}</p>
                  </div>
                  <div>
                    <span className="text-gray-500 text-sm">Age</span>
                    <p className="font-medium">{age ? `${age} years` : 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-gray-500 text-sm">Date of Birth</span>
                    <p className="font-medium">{child?.dob ? formatDate(child.dob) : 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-gray-500 text-sm">School</span>
                    <p className="font-medium">{child?.school || lead.school || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-gray-500 text-sm">Source</span>
                    <p className="font-medium">{lead.source || 'N/A'}</p>
                  </div>
                </div>
              </div>

              {/* Parent Information */}
              {lead.parents && lead.parents.length > 0 && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Parent Information</h3>
                  <div className="space-y-3">
                    {lead.parents.map((parent, idx) => (
                      <div key={idx} className="bg-gray-50 p-4 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold">{parent.name}</span>
                            {parent.is_primary && (
                              <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded">Primary</span>
                            )}
                          </div>
                          <button
                            onClick={() => {
                              setSelectedParent(parent);
                              setShowEditParentModal(true);
                            }}
                            className="text-sm px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition"
                          >
                            Edit
                          </button>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div>
                            <span className="text-gray-500">Phone:</span>{' '}
                            <a href={`tel:${parent.phone}`} className="text-blue-600 font-medium">{parent.phone}</a>
                          </div>
                          <div>
                            <span className="text-gray-500">Email:</span>{' '}
                            <span className="font-medium">{parent.email || '-'}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Discovery Information */}
              {(lead.source || lead.preferred_schedule || lead.parent_expectations || lead.discovery_notes) && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Discovery Information</h3>
                  <div className="grid grid-cols-2 gap-4">
                    {lead.source && (
                      <div>
                        <span className="text-gray-500 text-sm">Source</span>
                        <p className="font-medium">{lead.source.replace(/_/g, ' ')}</p>
                      </div>
                    )}
                    {lead.preferred_schedule && (
                      <div>
                        <span className="text-gray-500 text-sm">Preferred Schedule</span>
                        <p className="font-medium">{lead.preferred_schedule}</p>
                      </div>
                    )}
                    {lead.parent_expectations && lead.parent_expectations.length > 0 && (
                      <div className="col-span-2">
                        <span className="text-gray-500 text-sm">Parent Expectations</span>
                        <div className="flex flex-wrap gap-2 mt-1">
                          {lead.parent_expectations.map((exp, idx) => (
                            <span key={idx} className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded">
                              {exp.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {lead.discovery_notes && (
                      <div className="col-span-2">
                        <span className="text-gray-500 text-sm">Discovery Notes</span>
                        <p className="font-medium">{lead.discovery_notes}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Intro Visits */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-4 border-b pb-2">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Intro Visits ({lead.intro_visits?.length || 0})
                  </h3>
                  {onScheduleIV && lead.status !== 'CONVERTED' && lead.status !== 'CLOSED_LOST' && (
                    <button
                      onClick={onScheduleIV}
                      className="px-3 py-1 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
                    >
                      Schedule IV
                    </button>
                  )}
                </div>
                {!lead.intro_visits || lead.intro_visits.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">No intro visits scheduled</p>
                ) : (
                  <div className="space-y-3">
                    {lead.intro_visits.map((iv: any) => (
                      <div key={iv.id} className="border rounded-lg p-4 bg-gray-50">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">IV #{iv.id}</span>
                            {iv.outcome && (
                              <span className={`px-2 py-0.5 text-xs rounded ${
                                iv.outcome === 'INTERESTED_ENROLL_NOW' ? 'bg-green-100 text-green-700' :
                                iv.outcome === 'INTERESTED_ENROLL_LATER' ? 'bg-yellow-100 text-yellow-700' :
                                iv.outcome === 'NO_SHOW' ? 'bg-gray-100 text-gray-700' :
                                'bg-red-100 text-red-700'
                              }`}>
                                {IV_OUTCOME_LABELS[iv.outcome as keyof typeof IV_OUTCOME_LABELS] || iv.outcome}
                              </span>
                            )}
                          </div>
                          {onUpdateIV && (
                            <button
                              onClick={() => onUpdateIV(iv as IntroVisit)}
                              className="text-blue-600 hover:text-blue-700 text-sm"
                            >
                              Update
                            </button>
                          )}
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div>
                            <span className="text-gray-500">Scheduled:</span>{' '}
                            <span className="font-medium">{formatDateTime(iv.scheduled_at)}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">Attended:</span>{' '}
                            <span className="font-medium">{formatDateTime(iv.attended_at)}</span>
                          </div>
                          {iv.outcome_notes && (
                            <div className="col-span-2">
                              <span className="text-gray-500">Notes:</span>{' '}
                              <span className="font-medium">{iv.outcome_notes}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Follow-ups */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-4 border-b pb-2">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Follow-ups ({lead.follow_ups?.length || 0})
                  </h3>
                  {onCreateFollowUp && lead.status !== 'CONVERTED' && lead.status !== 'CLOSED_LOST' && (
                    <button
                      onClick={onCreateFollowUp}
                      className="px-3 py-1 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700"
                    >
                      Create Follow-up
                    </button>
                  )}
                </div>
                {!lead.follow_ups || lead.follow_ups.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">No follow-ups created</p>
                ) : (
                  <div className="space-y-3">
                    {lead.follow_ups.map((followUp: any) => (
                      <div key={followUp.id} className="border rounded-lg p-4 bg-gray-50">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">Follow-up #{followUp.id}</span>
                            <span className={`px-2 py-0.5 text-xs rounded ${
                              followUp.status === 'COMPLETED' ? 'bg-green-100 text-green-700' :
                              followUp.status === 'CANCELLED' ? 'bg-gray-100 text-gray-700' :
                              'bg-yellow-100 text-yellow-700'
                            }`}>
                              {followUp.status}
                            </span>
                            {followUp.outcome && (
                              <span className={`px-2 py-0.5 text-xs rounded ${
                                followUp.outcome === 'ENROLLED' ? 'bg-green-100 text-green-700' :
                                followUp.outcome === 'LOST' ? 'bg-red-100 text-red-700' :
                                'bg-blue-100 text-blue-700'
                              }`}>
                                {FOLLOW_UP_OUTCOME_LABELS[followUp.outcome as keyof typeof FOLLOW_UP_OUTCOME_LABELS] || followUp.outcome}
                              </span>
                            )}
                          </div>
                          {onUpdateFollowUp && (
                            <button
                              onClick={() => onUpdateFollowUp(followUp as FollowUp)}
                              className="text-blue-600 hover:text-blue-700 text-sm"
                            >
                              Update
                            </button>
                          )}
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div>
                            <span className="text-gray-500">Scheduled:</span>{' '}
                            <span className="font-medium">{formatDateTime(followUp.scheduled_date)}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">Completed:</span>{' '}
                            <span className="font-medium">{formatDateTime(followUp.completed_at)}</span>
                          </div>
                          {followUp.notes && (
                            <div className="col-span-2">
                              <span className="text-gray-500">Notes:</span>{' '}
                              <span className="font-medium">{followUp.notes}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Closure Information */}
              {lead.status === 'CLOSED_LOST' && lead.closed_reason && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-red-900 mb-2">Lead Closed</h3>
                  <p className="text-sm text-red-700 mb-1">
                    <span className="font-medium">Reason:</span> {lead.closed_reason}
                  </p>
                  <p className="text-sm text-red-700">
                    <span className="font-medium">Closed on:</span> {formatDate(lead.closed_at)}
                  </p>
                </div>
              )}
            </div>
          ) : (
            /* Activity Timeline Tab */
            <div className="space-y-1">
              {loadingActivities ? (
                <div className="text-center py-8 text-gray-500">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
                  Loading activity log...
                </div>
              ) : activities.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>No activity recorded yet</p>
                </div>
              ) : (
                <div className="relative">
                  {/* Timeline line */}
                  <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-200"></div>

                  {activities.map((activity, idx) => (
                    <div key={activity.id} className="relative flex gap-4 pb-6">
                      {/* Timeline dot */}
                      <div className={`relative z-10 w-10 h-10 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                        ACTIVITY_TYPE_COLORS[activity.activity_type] || 'bg-gray-100 text-gray-600'
                      }`}>
                        {activities.length - idx}
                      </div>

                      {/* Content */}
                      <div className="bg-white rounded-lg shadow-sm border p-4 flex-1">
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              {activity.description}
                            </p>
                            <div className="flex items-center gap-3 mt-1">
                              <span className="text-xs text-gray-500">
                                by <span className="font-medium text-gray-700">{activity.performed_by_name || `User #${activity.performed_by_id}`}</span>
                              </span>
                              <span className="text-xs text-gray-400">
                                {formatDateTime(activity.performed_at)}
                              </span>
                            </div>
                          </div>
                          {activity.new_value && (
                            <span className={`px-2 py-0.5 text-xs rounded flex-shrink-0 ${
                              STATUS_CONFIGS[activity.new_value as keyof typeof STATUS_CONFIGS]?.color || 'bg-gray-100 text-gray-600'
                            }`}>
                              {STATUS_CONFIGS[activity.new_value as keyof typeof STATUS_CONFIGS]?.label || activity.new_value}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="bg-gray-50 border-t p-4 flex justify-between items-center">
          <div className="flex gap-2">
            {onCloseLead && lead.status !== 'CLOSED_LOST' && lead.status !== 'CONVERTED' && (
              <button
                onClick={onCloseLead}
                className="px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-50"
              >
                Close Lead
              </button>
            )}
          </div>
          <div className="flex gap-3">
            {onRefresh && (
              <button
                onClick={() => { onRefresh(); fetchActivities(); }}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100"
              >
                Refresh
              </button>
            )}
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>

      {/* Edit Child Modal */}
      {showEditChildModal && child && (
        <EditChildModal
          child={child}
          onClose={() => setShowEditChildModal(false)}
          onSuccess={() => {
            setShowEditChildModal(false);
            if (onRefresh) {
              onRefresh();
              fetchActivities();
            }
          }}
        />
      )}

      {/* Edit Parent Modal */}
      {showEditParentModal && selectedParent && (
        <EditParentModal
          parent={selectedParent}
          onClose={() => {
            setShowEditParentModal(false);
            setSelectedParent(null);
          }}
          onSuccess={() => {
            setShowEditParentModal(false);
            setSelectedParent(null);
            if (onRefresh) {
              onRefresh();
              fetchActivities();
            }
          }}
        />
      )}
    </div>
  );
}
