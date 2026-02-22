'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { useCenterContext } from '@/hooks/useCenterContext';
import { useAuth } from '@/contexts/AuthContext';
import type {
  Lead,
  LeadDetail,
  LeadStatus,
  IntroVisit,
  FollowUp,
  PaginatedLeadsResponse,
} from '@/types/leads';
import { STATUS_CONFIGS } from '@/types/leads';
import PageHeader from '@/components/ui/PageHeader';
import LoadingState from '@/components/ui/LoadingState';
import EnquiryFormModal from '@/components/leads/EnquiryFormModal';
import LeadDetailModal from '@/components/leads/LeadDetailModal';
import ScheduleIVModal from '@/components/leads/ScheduleIVModal';
import UpdateIVModal from '@/components/leads/UpdateIVModal';
import CreateFollowUpModal from '@/components/leads/CreateFollowUpModal';
import UpdateFollowUpModal from '@/components/leads/UpdateFollowUpModal';
import CloseLeadModal from '@/components/leads/CloseLeadModal';
import ConvertToEnrollmentModal from '@/components/leads/ConvertToEnrollmentModal';

export default function EnhancedLeadsPage() {
  const { selectedCenter } = useCenterContext();
  const { user } = useAuth();
  const isSuperAdmin = user?.role === 'SUPER_ADMIN';

  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  const [selectedStatus, setSelectedStatus] = useState<LeadStatus | 'ALL'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [totalLeads, setTotalLeads] = useState(0);
  const [pageSize] = useState(50);

  // Status counts (these remain constant regardless of filters)
  const [statusCounts, setStatusCounts] = useState<Record<string, number>>({});

  // Modal states
  const [showEnquiryModal, setShowEnquiryModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showScheduleIVModal, setShowScheduleIVModal] = useState(false);
  const [showUpdateIVModal, setShowUpdateIVModal] = useState(false);
  const [showFollowUpModal, setShowFollowUpModal] = useState(false);
  const [showUpdateFollowUpModal, setShowUpdateFollowUpModal] = useState(false);
  const [showCloseModal, setShowCloseModal] = useState(false);
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [selectedLeadDetail, setSelectedLeadDetail] = useState<LeadDetail | null>(null);
  const [selectedIntroVisit, setSelectedIntroVisit] = useState<IntroVisit | null>(null);
  const [selectedFollowUp, setSelectedFollowUp] = useState<FollowUp | null>(null);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
      setCurrentPage(1);
    }, 400);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Fetch status counts only when center changes
  useEffect(() => {
    if (selectedCenter) {
      fetchStatusCounts();
    }
  }, [selectedCenter]);

  // Fetch leads when filters change
  useEffect(() => {
    if (selectedCenter) {
      fetchLeads();
    }
  }, [selectedCenter, currentPage, selectedStatus, debouncedSearch]);

  const fetchStatusCounts = async () => {
    if (!selectedCenter?.id) return;

    try {
      const params = new URLSearchParams({
        center_id: selectedCenter.id.toString(),
        exclude_statuses: 'CONVERTED',
      });

      const counts = await api.get<Record<string, number>>(`/api/v1/leads/stats/status-counts?${params.toString()}`);
      setStatusCounts(counts);
    } catch (err) {
      console.error('Failed to fetch status counts:', err);
      // Don't set error state, just log it
    }
  };

  const fetchLeads = async () => {
    if (!selectedCenter?.id) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const params = new URLSearchParams({
        center_id: selectedCenter.id.toString(),
        page: currentPage.toString(),
        page_size: pageSize.toString(),
        exclude_statuses: 'CONVERTED',
      });

      if (selectedStatus !== 'ALL') {
        params.append('status', selectedStatus);
      }

      if (debouncedSearch) {
        params.append('search', debouncedSearch);
      }

      const data = await api.get<PaginatedLeadsResponse>(`/api/v1/leads/list/paginated?${params.toString()}`);
      setLeads(data.leads);
      setTotalPages(data.total_pages);
      setTotalLeads(data.total);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch leads');
    } finally {
      setLoading(false);
    }
  };

  const fetchLeadDetails = async (leadId: number) => {
    try {
      const data = await api.get<LeadDetail>(`/api/v1/leads/${leadId}/details`);
      setSelectedLeadDetail(data);
    } catch (err) {
      console.error('Failed to fetch lead details:', err);
      alert('Failed to load lead details');
    }
  };

  const handleViewLead = async (lead: Lead) => {
    setSelectedLead(lead);
    await fetchLeadDetails(lead.id);
    setShowDetailModal(true);
  };

  const handleScheduleIV = (lead: Lead) => {
    setSelectedLead(lead);
    setShowScheduleIVModal(true);
  };

  const handleUpdateIV = (lead: Lead, introVisit: IntroVisit) => {
    setSelectedLead(lead);
    setSelectedIntroVisit(introVisit);
    setShowUpdateIVModal(true);
  };

  const handleCreateFollowUp = (lead: Lead) => {
    setSelectedLead(lead);
    setShowFollowUpModal(true);
  };

  const handleUpdateFollowUp = (lead: Lead, followUp: FollowUp) => {
    setSelectedLead(lead);
    setSelectedFollowUp(followUp);
    setShowUpdateFollowUpModal(true);
  };

  const handleCloseLead = (lead: Lead) => {
    setSelectedLead(lead);
    setShowCloseModal(true);
  };

  // Open enrollment modal
  const handleEnroll = (lead: Lead) => {
    setSelectedLead(lead);
    setShowEnrollModal(true);
  };

  // Quick action: Mark IV Completed
  const handleQuickIVCompleted = async (lead: Lead) => {
    if (!confirm(`Mark "${getLeadName(lead)}" IV as Completed?`)) return;
    setActionLoading(lead.id);
    try {
      await api.patch(`/api/v1/leads/${lead.id}/status`, {
        status: 'IV_COMPLETED',
        notes: 'IV marked as completed',
      });
      fetchLeads();
      fetchStatusCounts();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update status');
    } finally {
      setActionLoading(null);
    }
  };

  // Quick action: Not Interested
  const handleQuickNotInterested = async (lead: Lead) => {
    if (!confirm(`Mark "${getLeadName(lead)}" as Not Interested?`)) return;
    setActionLoading(lead.id);
    try {
      await api.post(`/api/v1/leads/${lead.id}/close`, {
        reason: 'Not Interested',
      });
      fetchLeads();
      fetchStatusCounts();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to close lead');
    } finally {
      setActionLoading(null);
    }
  };

  // Delete lead (Super Admin only)
  const handleDeleteLead = async () => {
    if (!selectedLead) return;
    setActionLoading(selectedLead.id);
    try {
      await api.delete(`/api/v1/leads/${selectedLead.id}`);
      setShowDeleteConfirm(false);
      setSelectedLead(null);
      fetchLeads();
      fetchStatusCounts();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete lead');
    } finally {
      setActionLoading(null);
    }
  };

  const handleSuccess = () => {
    fetchLeads();
    fetchStatusCounts(); // Refresh counts when status changes
    setShowEnquiryModal(false);
    setShowDetailModal(false);
    setShowScheduleIVModal(false);
    setShowUpdateIVModal(false);
    setShowFollowUpModal(false);
    setShowUpdateFollowUpModal(false);
    setShowCloseModal(false);
    setShowEnrollModal(false);
    setSelectedLead(null);
    setSelectedLeadDetail(null);
    setSelectedIntroVisit(null);
    setSelectedFollowUp(null);
  };

  const getLeadName = (lead: Lead): string => {
    return (lead as any).child_name || `${lead.child?.first_name || ''} ${lead.child?.last_name || ''}`.trim() || 'N/A';
  };

  const isTerminal = (status: LeadStatus): boolean => {
    return status === 'CONVERTED' || status === 'CLOSED_LOST';
  };

  // Get context-aware quick actions based on lead status
  const getQuickActions = (lead: Lead) => {
    if (isTerminal(lead.status)) return null;

    const actions: JSX.Element[] = [];
    const isLoading = actionLoading === lead.id;

    // Schedule IV - available for most non-terminal statuses
    if (['ENQUIRY_RECEIVED', 'DISCOVERY_COMPLETED', 'IV_NO_SHOW', 'FOLLOW_UP_PENDING'].includes(lead.status)) {
      actions.push(
        <button
          key="schedule-iv"
          onClick={(e) => { e.stopPropagation(); handleScheduleIV(lead); }}
          disabled={isLoading}
          className="px-2 py-1 text-xs font-medium rounded bg-yellow-100 text-yellow-800 hover:bg-yellow-200 transition whitespace-nowrap"
          title="Schedule Intro Visit"
        >
          Schedule IV
        </button>
      );
    }

    // IV Completed - only when IV is scheduled
    if (lead.status === 'IV_SCHEDULED') {
      actions.push(
        <button
          key="iv-completed"
          onClick={(e) => { e.stopPropagation(); handleQuickIVCompleted(lead); }}
          disabled={isLoading}
          className="px-2 py-1 text-xs font-medium rounded bg-purple-100 text-purple-800 hover:bg-purple-200 transition whitespace-nowrap"
          title="Mark IV as Completed"
        >
          IV Done
        </button>
      );
    }

    // Follow Up - available for most statuses
    if (['ENQUIRY_RECEIVED', 'DISCOVERY_COMPLETED', 'IV_COMPLETED', 'IV_NO_SHOW', 'FOLLOW_UP_PENDING'].includes(lead.status)) {
      actions.push(
        <button
          key="follow-up"
          onClick={(e) => { e.stopPropagation(); handleCreateFollowUp(lead); }}
          disabled={isLoading}
          className="px-2 py-1 text-xs font-medium rounded bg-orange-100 text-orange-800 hover:bg-orange-200 transition whitespace-nowrap"
          title="Create Follow-up"
        >
          Follow Up
        </button>
      );
    }

    // Enrolled - available after IV completed or follow-up
    if (['IV_COMPLETED', 'FOLLOW_UP_PENDING'].includes(lead.status)) {
      actions.push(
        <button
          key="enrolled"
          onClick={(e) => { e.stopPropagation(); handleEnroll(lead); }}
          disabled={isLoading}
          className="px-2 py-1 text-xs font-medium rounded bg-green-100 text-green-800 hover:bg-green-200 transition whitespace-nowrap"
          title="Mark as Enrolled"
        >
          Enrolled
        </button>
      );
    }

    // Not Interested - available for all non-terminal
    actions.push(
      <button
        key="not-interested"
        onClick={(e) => { e.stopPropagation(); handleQuickNotInterested(lead); }}
        disabled={isLoading}
        className="px-2 py-1 text-xs font-medium rounded bg-red-100 text-red-800 hover:bg-red-200 transition whitespace-nowrap"
        title="Mark as Not Interested"
      >
        Not Interested
      </button>
    );

    return actions;
  };

  if (!selectedCenter) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500 mb-4">Please select a center first</p>
          <a href="/dashboard" className="btn-primary inline-block">
            Go to Dashboard
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* Header */}
      <PageHeader
        title="Leads Management"
        subtitle="Track leads from enquiry through conversion"
        action={
          <button
            onClick={() => setShowEnquiryModal(true)}
            className="btn-success"
          >
            + New Enquiry
          </button>
        }
      />

      {/* Status Filter Cards */}
      <div className="mb-6">
        <div className="card-static card-body">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Filter by Status</h3>
          <div className="grid grid-cols-3 md:grid-cols-5 lg:grid-cols-9 gap-3">
            <button
              onClick={() => {
                setSelectedStatus('ALL');
                setCurrentPage(1);
              }}
              className={`p-3 rounded-lg border-2 transition text-center ${
                selectedStatus === 'ALL'
                  ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
              }`}
            >
              <div className="text-2xl font-bold text-gray-900">{totalLeads || 0}</div>
              <div className="text-xs font-medium text-gray-600 mt-1">All Leads</div>
            </button>

            {Object.values(STATUS_CONFIGS).map((config) => {
              const isActive = selectedStatus === config.value;
              const count = statusCounts[config.value] || 0;
              return (
                <button
                  key={config.value}
                  onClick={() => {
                    setSelectedStatus(config.value);
                    setCurrentPage(1);
                  }}
                  className={`p-3 rounded-lg border-2 transition text-center ${
                    isActive
                      ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                      : 'border-gray-200 hover:border-gray-300 bg-white'
                  }`}
                >
                  <div className="text-2xl font-bold text-gray-900">{count}</div>
                  <div className={`text-xs font-semibold px-2 py-1 rounded mt-1 ${config.color}`}>
                    {config.label}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="card-static card-body">
          <div className="relative">
            <input
              type="text"
              placeholder="Search by child name, parent name, or phone..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input w-full pr-10"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition"
                title="Clear search"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Leads Table */}
      <div className="table-wrapper">
        {loading ? (
          <LoadingState message="Loading leads..." />
        ) : error ? (
          <div className="p-12 text-center">
            <div className="text-red-500 mb-4">Error: {error}</div>
            <button
              onClick={fetchLeads}
              className="btn-primary"
            >
              Retry
            </button>
          </div>
        ) : leads.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            <p className="text-lg font-medium mb-2">
              {selectedStatus === 'ALL' ? 'No leads found' : `No ${STATUS_CONFIGS[selectedStatus as LeadStatus]?.label} leads`}
            </p>
            {selectedStatus === 'ALL' && (
              <button
                onClick={() => setShowEnquiryModal(true)}
                className="mt-4 btn-success"
              >
                Create your first lead
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="table-header-cell">
                    Enquiry ID
                  </th>
                  <th className="table-header-cell">
                    Child Name
                  </th>
                  <th className="table-header-cell">
                    Source
                  </th>
                  <th className="table-header-cell">
                    Status
                  </th>
                  <th className="table-header-cell">
                    Created
                  </th>
                  <th className="table-header-cell">
                    Quick Actions
                  </th>
                  <th className="table-header-cell">
                    {/* View / Delete */}
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {leads.map((lead) => (
                  <tr key={lead.id} className="table-row">
                    <td className="table-cell whitespace-nowrap">
                      <span className="text-sm font-mono font-medium text-gray-900">
                        {(lead as any).enquiry_id || lead.child?.enquiry_id || 'N/A'}
                      </span>
                    </td>
                    <td className="table-cell whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {getLeadName(lead)}
                      </div>
                    </td>
                    <td className="table-cell whitespace-nowrap text-sm text-gray-500">
                      {lead.source?.replace(/_/g, ' ') || '-'}
                    </td>
                    <td className="table-cell whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${STATUS_CONFIGS[lead.status]?.color || 'bg-gray-100 text-gray-800'}`}>
                        {STATUS_CONFIGS[lead.status]?.label || lead.status}
                      </span>
                    </td>
                    <td className="table-cell whitespace-nowrap text-sm text-gray-500">
                      {new Date(lead.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}
                    </td>
                    <td className="table-cell">
                      <div className="flex flex-wrap gap-1">
                        {actionLoading === lead.id ? (
                          <span className="text-xs text-gray-400">Updating...</span>
                        ) : (
                          getQuickActions(lead)
                        )}
                      </div>
                    </td>
                    <td className="table-cell whitespace-nowrap">
                      <div className="flex gap-2 items-center">
                        <button
                          onClick={() => handleViewLead(lead)}
                          className="px-3 py-1 text-xs font-medium rounded bg-blue-100 text-blue-800 hover:bg-blue-200 transition"
                        >
                          View
                        </button>
                        {isSuperAdmin && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedLead(lead);
                              setShowDeleteConfirm(true);
                            }}
                            className="px-3 py-1 text-xs font-medium rounded bg-red-100 text-red-700 hover:bg-red-200 transition"
                            title="Delete Lead (Super Admin)"
                          >
                            Delete
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Controls */}
        {!loading && !error && totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Page <span className="font-medium">{currentPage}</span> of{' '}
              <span className="font-medium">{totalPages}</span>
              {' '}({totalLeads} total)
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage(1)}
                disabled={currentPage === 1}
                className="btn-ghost disabled:opacity-50 disabled:cursor-not-allowed"
              >
                First
              </button>
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Prev
              </button>
              <div className="px-4 py-2 bg-blue-50 text-blue-700 font-medium rounded-lg border border-blue-200">
                {currentPage}
              </div>
              <button
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
                className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
              <button
                onClick={() => setCurrentPage(totalPages)}
                disabled={currentPage === totalPages}
                className="btn-ghost disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Last
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && selectedLead && (
        <div className="modal-backdrop">
          <div className="modal-panel max-w-md w-full p-6">
            <h3 className="modal-header">Delete Lead</h3>
            <p className="text-gray-600 mb-1">
              Are you sure you want to permanently delete this lead?
            </p>
            <p className="text-sm font-medium text-gray-800 mb-4">
              {getLeadName(selectedLead)} ({(selectedLead as any).enquiry_id || 'N/A'})
            </p>
            <p className="text-xs text-red-600 mb-6">
              This will delete all related intro visits, follow-ups, and activity logs. This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => {
                  setShowDeleteConfirm(false);
                  setSelectedLead(null);
                }}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteLead}
                disabled={actionLoading === selectedLead.id}
                className="btn-danger disabled:opacity-50"
              >
                {actionLoading === selectedLead.id ? 'Deleting...' : 'Delete Permanently'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modals */}
      {showEnquiryModal && (
        <EnquiryFormModal
          onClose={() => setShowEnquiryModal(false)}
          onSuccess={handleSuccess}
          centerId={selectedCenter.id}
        />
      )}

      {showDetailModal && selectedLead && selectedLeadDetail && (
        <LeadDetailModal
          lead={selectedLead}
          detail={selectedLeadDetail}
          onClose={() => {
            setShowDetailModal(false);
            setSelectedLead(null);
            setSelectedLeadDetail(null);
          }}
          onScheduleIV={() => {
            setShowDetailModal(false);
            setShowScheduleIVModal(true);
          }}
          onUpdateIV={(iv) => handleUpdateIV(selectedLead, iv)}
          onCreateFollowUp={() => {
            setShowDetailModal(false);
            setShowFollowUpModal(true);
          }}
          onUpdateFollowUp={(fu) => handleUpdateFollowUp(selectedLead, fu)}
          onCloseLead={() => {
            setShowDetailModal(false);
            setShowCloseModal(true);
          }}
          onRefresh={() => fetchLeadDetails(selectedLead.id)}
        />
      )}

      {showScheduleIVModal && selectedLead && (
        <ScheduleIVModal
          leadId={selectedLead.id}
          onClose={() => {
            setShowScheduleIVModal(false);
            setSelectedLead(null);
          }}
          onSuccess={handleSuccess}
        />
      )}

      {showUpdateIVModal && selectedLead && selectedIntroVisit && (
        <UpdateIVModal
          ivId={selectedIntroVisit.id}
          onClose={() => {
            setShowUpdateIVModal(false);
            setSelectedLead(null);
            setSelectedIntroVisit(null);
          }}
          onSuccess={handleSuccess}
        />
      )}

      {showFollowUpModal && selectedLead && (
        <CreateFollowUpModal
          leadId={selectedLead.id}
          onClose={() => {
            setShowFollowUpModal(false);
            setSelectedLead(null);
          }}
          onSuccess={handleSuccess}
        />
      )}

      {showUpdateFollowUpModal && selectedLead && selectedFollowUp && (
        <UpdateFollowUpModal
          followUpId={selectedFollowUp.id}
          onClose={() => {
            setShowUpdateFollowUpModal(false);
            setSelectedLead(null);
            setSelectedFollowUp(null);
          }}
          onSuccess={handleSuccess}
        />
      )}

      {showCloseModal && selectedLead && (
        <CloseLeadModal
          leadId={selectedLead.id}
          onClose={() => {
            setShowCloseModal(false);
            setSelectedLead(null);
          }}
          onSuccess={handleSuccess}
        />
      )}

      {showEnrollModal && selectedLead && (
        <ConvertToEnrollmentModal
          leadId={selectedLead.id}
          childId={selectedLead.child_id}
          childName={getLeadName(selectedLead)}
          onClose={() => {
            setShowEnrollModal(false);
            setSelectedLead(null);
          }}
          onSuccess={handleSuccess}
        />
      )}
    </div>
  );
}
