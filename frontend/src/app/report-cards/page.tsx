'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { useCenter } from '@/contexts/CenterContext';
import type { ReportCard, Child } from '@/types';

export default function ReportCardsPage() {
  const { selectedCenter } = useCenter();
  const [reportCards, setReportCards] = useState<ReportCard[]>([]);
  const [children, setChildren] = useState<Child[]>([]);
  const [selectedChild, setSelectedChild] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [selectedReport, setSelectedReport] = useState<ReportCard | null>(null);

  useEffect(() => {
    fetchChildren();
    fetchReportCards();
  }, [selectedCenter]);

  useEffect(() => {
    if (selectedChild) {
      fetchReportCards(selectedChild);
    } else {
      fetchReportCards();
    }
  }, [selectedChild]);

  const fetchChildren = async () => {
    try {
      const centerParam = selectedCenter ? `&center_id=${selectedCenter.id}` : '';
      const enrollments = await api.get<any[]>(`/api/v1/enrollments?status=ACTIVE${centerParam}`);
      const uniqueChildren = Array.from(
        new Map(enrollments.map((e) => [e.child.id, e.child])).values()
      ) as Child[];
      setChildren(uniqueChildren);
    } catch (err) {
      console.error('Failed to fetch children:', err);
    }
  };

  const fetchReportCards = async (childId?: number) => {
    try {
      setLoading(true);
      const centerParam = selectedCenter ? `center_id=${selectedCenter.id}` : '';
      const childParam = childId ? `child_id=${childId}` : '';
      const params = [centerParam, childParam].filter(Boolean).join('&');
      const endpoint = `/api/v1/report-cards${params ? `?${params}` : ''}`;
      const data = await api.get<ReportCard[]>(endpoint);
      setReportCards(data);
    } catch (err) {
      console.error('Failed to fetch report cards:', err);
    } finally {
      setLoading(false);
    }
  };

  const viewReport = async (reportId: number) => {
    try {
      const report = await api.get<ReportCard>(`/api/v1/report-cards/${reportId}`);
      setSelectedReport(report);
    } catch (err) {
      console.error('Failed to fetch report card:', err);
      alert('Failed to load report card');
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Report Cards</h1>
          <p className="text-gray-600">Generate and view student progress reports</p>
        </div>
        <button
          onClick={() => setShowGenerateModal(true)}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
        >
          + Generate Report Card
        </button>
      </div>

      {/* Filter */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Filter by Child
        </label>
        <select
          value={selectedChild || ''}
          onChange={(e) => setSelectedChild(e.target.value ? Number(e.target.value) : null)}
          className="w-full md:w-96 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Children</option>
          {children.map((child) => (
            <option key={child.id} value={child.id}>
              {child.first_name} {child.last_name || ''}
            </option>
          ))}
        </select>
      </div>

      {/* Report Cards List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading report cards...</div>
        ) : reportCards.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No report cards found. Generate your first report card to get started!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Child Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Period
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Generated
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {reportCards.map((report) => (
                  <tr key={report.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {report.child?.first_name} {report.child?.last_name || ''}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(report.period_start).toLocaleDateString()} -{' '}
                      {new Date(report.period_end).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(report.generated_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => viewReport(report.id)}
                        className="text-blue-600 hover:text-blue-900 mr-3"
                      >
                        View
                      </button>
                      <button
                        onClick={() => window.print()}
                        className="text-green-600 hover:text-green-900"
                      >
                        Print
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Generate Report Card Modal */}
      {showGenerateModal && (
        <GenerateReportModal
          children={children}
          onClose={() => setShowGenerateModal(false)}
          onSuccess={() => {
            setShowGenerateModal(false);
            fetchReportCards(selectedChild || undefined);
          }}
        />
      )}

      {/* View Report Modal */}
      {selectedReport && (
        <ViewReportModal
          report={selectedReport}
          onClose={() => setSelectedReport(null)}
        />
      )}
    </div>
  );
}

function GenerateReportModal({
  children,
  onClose,
  onSuccess,
}: {
  children: Child[];
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState({
    child_id: '',
    period_start: '',
    period_end: '',
    summary_notes: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      await api.post('/api/v1/report-cards/generate', {
        child_id: Number(formData.child_id),
        period_start: formData.period_start,
        period_end: formData.period_end,
        summary_notes: formData.summary_notes || null,
      });
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate report card');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-md w-full p-6">
        <h2 className="text-2xl font-bold mb-4">Generate Report Card</h2>
        {error && <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Select Child *
            </label>
            <select
              required
              value={formData.child_id}
              onChange={(e) => setFormData({ ...formData, child_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">-- Select a child --</option>
              {children.map((child) => (
                <option key={child.id} value={child.id}>
                  {child.first_name} {child.last_name || ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Period Start Date *
            </label>
            <input
              type="date"
              required
              value={formData.period_start}
              onChange={(e) => setFormData({ ...formData, period_start: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Period End Date *
            </label>
            <input
              type="date"
              required
              value={formData.period_end}
              onChange={(e) => setFormData({ ...formData, period_end: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Summary Notes
            </label>
            <textarea
              value={formData.summary_notes}
              onChange={(e) => setFormData({ ...formData, summary_notes: e.target.value })}
              rows={3}
              placeholder="Overall assessment and comments..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex gap-3 mt-6">
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium disabled:opacity-50"
            >
              {submitting ? 'Generating...' : 'Generate Report'}
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

function ViewReportModal({
  report,
  onClose,
}: {
  report: ReportCard;
  onClose: () => void;
}) {
  const snapshot = report.skill_snapshot as any;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">Report Card</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-semibold text-lg mb-2">
              {report.child?.first_name} {report.child?.last_name || ''}
            </h3>
            <div className="text-sm text-gray-600">
              <p>
                Period: {new Date(report.period_start).toLocaleDateString()} -{' '}
                {new Date(report.period_end).toLocaleDateString()}
              </p>
              <p>Generated: {new Date(report.generated_at).toLocaleDateString()}</p>
            </div>
            {report.summary_notes && (
              <div className="mt-3 p-3 bg-white rounded border border-gray-200">
                <p className="text-sm">{report.summary_notes}</p>
              </div>
            )}
          </div>

          {snapshot?.summary && (
            <div className="mb-6 grid grid-cols-4 gap-4">
              <div className="bg-gray-100 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {snapshot.summary.not_started || 0}
                </div>
                <div className="text-sm text-gray-600">Not Started</div>
              </div>
              <div className="bg-blue-100 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-blue-900">
                  {snapshot.summary.in_progress || 0}
                </div>
                <div className="text-sm text-blue-700">In Progress</div>
              </div>
              <div className="bg-green-100 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-green-900">
                  {snapshot.summary.achieved || 0}
                </div>
                <div className="text-sm text-green-700">Achieved</div>
              </div>
              <div className="bg-purple-100 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-purple-900">
                  {snapshot.summary.mastered || 0}
                </div>
                <div className="text-sm text-purple-700">Mastered</div>
              </div>
            </div>
          )}

          <div>
            <h3 className="font-semibold text-lg mb-3">Skills Progress</h3>
            <div className="space-y-2">
              {snapshot?.skills?.map((skill: any, index: number) => (
                <div
                  key={index}
                  className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{skill.skill_name}</h4>
                      {skill.category && (
                        <span className="text-xs text-gray-500">{skill.category}</span>
                      )}
                      {skill.notes && (
                        <p className="text-sm text-gray-600 mt-1">{skill.notes}</p>
                      )}
                    </div>
                    <div className="ml-4">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          skill.level === 'MASTERED'
                            ? 'bg-purple-100 text-purple-800'
                            : skill.level === 'ACHIEVED'
                            ? 'bg-green-100 text-green-800'
                            : skill.level === 'IN_PROGRESS'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {skill.level.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 flex gap-3">
            <button
              onClick={() => window.print()}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
            >
              Print Report
            </button>
            <button
              onClick={onClose}
              className="px-6 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition font-medium"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
