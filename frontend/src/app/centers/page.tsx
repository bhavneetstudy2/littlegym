'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useCenterContext } from '@/hooks/useCenterContext';
import type { Center, CenterStats } from '@/types/center';
import { api } from '@/lib/api';
import EmptyState from '@/components/ui/EmptyState';

export default function CentersPage() {
  const router = useRouter();
  const { centers, loading, setSelectedCenter } = useCenterContext();
  const [centerStats, setCenterStats] = useState<Record<number, CenterStats>>({});
  const [loadingStats, setLoadingStats] = useState<Record<number, boolean>>({});

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
            onClick: () => {
              // TODO: Open create center modal
              alert('Create center modal coming soon');
            }
          }}
        />
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
          onClick={() => alert('Create center modal coming soon')}
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
    </div>
  );
}
