'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useCenterContext } from '@/hooks/useCenterContext';
import { api } from '@/lib/api';
import { Center } from '@/types/center';

interface CenterStats {
  total_leads: number;
  total_enrollments: number;
  total_batches: number;
  total_users: number;
  active_enrollments: number;
}

export default function CenterDetailPage() {
  const params = useParams();
  const router = useRouter();
  const centerId = parseInt(params.id as string);
  const { setSelectedCenter } = useCenterContext();

  const [center, setCenter] = useState<Center | null>(null);
  const [stats, setStats] = useState<CenterStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCenterDetails();
  }, [centerId]);

  const fetchCenterDetails = async () => {
    try {
      setLoading(true);
      const [centerData, statsData] = await Promise.all([
        api.get<Center>(`/api/v1/centers/${centerId}`),
        api.get<CenterStats>(`/api/v1/centers/${centerId}/stats`)
      ]);
      setCenter(centerData);
      setStats(statsData);
    } catch (error) {
      console.error('Failed to fetch center details:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEnterCenter = () => {
    if (center) {
      setSelectedCenter(center);
      router.push('/dashboard');
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-gray-500">Loading center details...</div>
      </div>
    );
  }

  if (!center) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-red-500">Center not found</div>
      </div>
    );
  }

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <button
              onClick={() => router.push('/centers')}
              className="text-gray-500 hover:text-gray-700"
            >
              ← Back to Centers
            </button>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">{center.name}</h1>
          <div className="flex items-center gap-3 mt-2">
            <span className="px-2.5 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded">
              {center.code}
            </span>
            {center.active ? (
              <span className="px-2.5 py-1 bg-green-100 text-green-800 text-sm font-medium rounded">
                Active
              </span>
            ) : (
              <span className="px-2.5 py-1 bg-gray-100 text-gray-800 text-sm font-medium rounded">
                Inactive
              </span>
            )}
          </div>
        </div>
        <button
          onClick={handleEnterCenter}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold"
        >
          Enter Center
        </button>
      </div>

      {/* Center Info */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Center Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-gray-500">Location</div>
            <div className="text-gray-900 font-medium">
              {center.city}, {center.state}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Address</div>
            <div className="text-gray-900 font-medium">{center.address}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Phone</div>
            <div className="text-gray-900 font-medium">{center.phone}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Email</div>
            <div className="text-gray-900 font-medium">{center.email}</div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="text-sm text-gray-500 mb-1">Total Leads</div>
            <div className="text-3xl font-bold text-gray-900">{stats.total_leads}</div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="text-sm text-gray-500 mb-1">Active Enrollments</div>
            <div className="text-3xl font-bold text-green-600">{stats.active_enrollments}</div>
            <div className="text-xs text-gray-500 mt-1">of {stats.total_enrollments} total</div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="text-sm text-gray-500 mb-1">Batches</div>
            <div className="text-3xl font-bold text-gray-900">{stats.total_batches}</div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="text-sm text-gray-500 mb-1">Users</div>
            <div className="text-3xl font-bold text-gray-900">{stats.total_users}</div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => {
              setSelectedCenter(center);
              router.push('/leads');
            }}
            className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition text-left"
          >
            <div className="text-2xl mb-2">👥</div>
            <div className="font-semibold text-gray-900">Manage Leads</div>
            <div className="text-sm text-gray-500">View and manage lead pipeline</div>
          </button>
          <button
            onClick={() => {
              setSelectedCenter(center);
              router.push('/enrollments');
            }}
            className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition text-left"
          >
            <div className="text-2xl mb-2">📋</div>
            <div className="font-semibold text-gray-900">Enrollments</div>
            <div className="text-sm text-gray-500">Manage student enrollments</div>
          </button>
          <button
            onClick={() => {
              setSelectedCenter(center);
              router.push('/attendance');
            }}
            className="p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition text-left"
          >
            <div className="text-2xl mb-2">✓</div>
            <div className="font-semibold text-gray-900">Attendance</div>
            <div className="text-sm text-gray-500">Mark class attendance</div>
          </button>
        </div>
      </div>
    </div>
  );
}
