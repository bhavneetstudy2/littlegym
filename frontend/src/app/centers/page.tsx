'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useCenterContext } from '@/hooks/useCenterContext';
import type { Center, CenterStats } from '@/types/center';
import { api } from '@/lib/api';
import EmptyState from '@/components/ui/EmptyState';

export default function CentersPage() {
  const router = useRouter();
  const { centers, loading, setSelectedCenter, refetchCenters } = useCenterContext();
  const [centerStats, setCenterStats] = useState<Record<number, CenterStats>>({});
  const [loadingStats, setLoadingStats] = useState<Record<number, boolean>>({});
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Fetch stats for a center when card is hovered or mounted
  const fetchCenterStats = async (centerId: number) => {
    if (centerStats[centerId] || loadingStats[centerId]) return;

    setLoadingStats(prev => ({ ...prev, [centerId]: true }));
    try {
      const stats = await api.get<CenterStats>(`/api/v1/centers/${centerId}/stats`);
      setCenterStats(prev => ({ ...prev, [centerId]: stats }));
    } catch (error) {
      console.error(`Failed to fetch stats for center ${centerId}:`, error);
    } finally {
      setLoadingStats(prev => ({ ...prev, [centerId]: false }));
    }
  };

  const handleViewCenter = (center: Center) => {
    setSelectedCenter(center);
    router.push(`/centers/${center.id}`);
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Centers</h1>
          <p className="text-gray-600">Manage all Little Gym centers</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map(i => (
            <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (centers.length === 0) {
    return (
      <div className="p-6">
        <EmptyState
          icon={
            <svg className="w-16 h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          }
          title="No Centers Found"
          description="Get started by creating your first center"
          action={{
            label: "+ New Center",
            onClick: () => setShowCreateModal(true)
          }}
        />
        {showCreateModal && (
          <AddCenterModal
            onClose={() => setShowCreateModal(false)}
            onSuccess={() => { setShowCreateModal(false); refetchCenters(); }}
          />
        )}
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Centers</h1>
          <p className="text-gray-600">Manage all Little Gym centers</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
        >
          + New Center
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {centers.map(center => {
          const stats = centerStats[center.id];

          return (
            <div
              key={center.id}
              onMouseEnter={() => fetchCenterStats(center.id)}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition cursor-pointer"
              onClick={() => handleViewCenter(center)}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    {center.name}
                  </h3>
                  {center.city && (
                    <p className="text-sm text-gray-600">
                      {center.city}{center.state ? `, ${center.state}` : ''}
                    </p>
                  )}
                  {center.code && (
                    <span className="inline-block mt-2 px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded">
                      {center.code}
                    </span>
                  )}
                </div>
                {center.active ? (
                  <span className="px-2 py-1 text-xs font-semibold bg-green-100 text-green-800 rounded-full">
                    Active
                  </span>
                ) : (
                  <span className="px-2 py-1 text-xs font-semibold bg-gray-100 text-gray-800 rounded-full">
                    Inactive
                  </span>
                )}
              </div>

              {stats ? (
                <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-gray-200">
                  <div>
                    <div className="flex items-center gap-2 text-gray-600 text-xs mb-1">
                      <span>🎯</span>
                      <span>Active Students</span>
                    </div>
                    <div className="text-2xl font-bold text-gray-900">
                      {stats.active_enrollments}
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center gap-2 text-gray-600 text-xs mb-1">
                      <span>📋</span>
                      <span>Total Leads</span>
                    </div>
                    <div className="text-2xl font-bold text-gray-900">
                      {stats.total_leads}
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center gap-2 text-gray-600 text-xs mb-1">
                      <span>👥</span>
                      <span>Batches</span>
                    </div>
                    <div className="text-2xl font-bold text-gray-900">
                      {stats.total_batches}
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center gap-2 text-gray-600 text-xs mb-1">
                      <span>👤</span>
                      <span>Users</span>
                    </div>
                    <div className="text-2xl font-bold text-gray-900">
                      {stats.total_users}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="text-sm text-gray-500 text-center py-2">
                    Hover to load stats...
                  </div>
                </div>
              )}

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleViewCenter(center);
                }}
                className="mt-4 w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition font-medium text-sm"
              >
                View Center →
              </button>
            </div>
          );
        })}
      </div>

      {showCreateModal && (
        <AddCenterModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => { setShowCreateModal(false); refetchCenters(); }}
        />
      )}
    </div>
  );
}

function AddCenterModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [formData, setFormData] = useState({
    name: '',
    city: '',
    address: '',
    phone: '',
    timezone: 'Asia/Kolkata',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await api.post('/api/v1/centers', formData);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create center');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-md w-full p-6">
        <h2 className="text-2xl font-bold mb-4">Add New Center</h2>
        {error && <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <input type="text" required value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">City *</label>
            <input type="text" required value={formData.city}
              onChange={(e) => setFormData({ ...formData, city: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Address *</label>
            <textarea required value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              rows={3} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Phone *</label>
            <input type="tel" required value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Timezone</label>
            <input type="text" value={formData.timezone}
              onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>
          <div className="flex gap-3 mt-6">
            <button type="submit" disabled={submitting}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium disabled:opacity-50">
              {submitting ? 'Creating...' : 'Create Center'}
            </button>
            <button type="button" onClick={onClose}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition font-medium">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
