'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useCenter } from '@/contexts/CenterContext';
import { api } from '@/lib/api';
import { Users, BookOpen, Calendar, Clock, Plus, ClipboardCheck, BarChart3, RefreshCw, ChevronLeft, Building2, ChevronRight } from 'lucide-react';
import PageHeader from '@/components/ui/PageHeader';
import StatCard from '@/components/ui/StatCard';
import LoadingState from '@/components/ui/LoadingState';

interface User {
  id: number;
  name: string;
  email: string;
  role: string;
  center_id: number | null;
}

interface DashboardStats {
  total_leads: number;
  active_enrollments: number;
  todays_classes: number;
  pending_renewals: number;
}

interface BatchSummary {
  id: number;
  name: string;
  age_min: number | null;
  age_max: number | null;
  days_of_week: string[];
  start_time: string | null;
  end_time: string | null;
  capacity: number | null;
  active_students: number;
}

const DAY_SHORT: Record<string, string> = {
  Mon: 'M', Tue: 'T', Wed: 'W', Thu: 'Th', Fri: 'F', Sat: 'Sa', Sun: 'Su',
};

function formatTime(t: string | null): string {
  if (!t) return '';
  const [h, m] = t.split(':').map(Number);
  const ampm = h >= 12 ? 'PM' : 'AM';
  const hour = h % 12 || 12;
  return `${hour}:${String(m).padStart(2, '0')} ${ampm}`;
}

function AgeRange({ min, max }: { min: number | null; max: number | null }) {
  if (!min && !max) return <span className="text-gray-400 text-xs">All ages</span>;
  if (min && max) return <span className="text-xs text-gray-500">{min}–{max} yrs</span>;
  if (min) return <span className="text-xs text-gray-500">{min}+ yrs</span>;
  return <span className="text-xs text-gray-500">Up to {max} yrs</span>;
}

export default function DashboardPage() {
  const router = useRouter();
  const { centers, selectedCenter, setSelectedCenter, loading: centersLoading } = useCenter();
  const [user, setUser] = useState<User | null>(null);
  const [stats, setStats] = useState<DashboardStats>({
    total_leads: 0,
    active_enrollments: 0,
    todays_classes: 0,
    pending_renewals: 0
  });
  const [statsLoading, setStatsLoading] = useState(true);
  const [batches, setBatches] = useState<BatchSummary[]>([]);
  const [batchesLoading, setBatchesLoading] = useState(false);

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (!userData) {
      router.push('/login');
      return;
    }
    setUser(JSON.parse(userData));
  }, [router]);

  // Fetch stats when center changes
  useEffect(() => {
    const fetchStats = async () => {
      if (!selectedCenter) {
        setStatsLoading(false);
        return;
      }
      setStatsLoading(true);
      try {
        const centerStats = await api.get<any>(`/api/v1/centers/${selectedCenter.id}/stats`);
        setStats({
          total_leads: centerStats.total_leads || 0,
          active_enrollments: centerStats.active_enrollments || 0,
          todays_classes: centerStats.todays_classes || 0,
          pending_renewals: centerStats.pending_renewals || 0
        });
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setStatsLoading(false);
      }
    };
    fetchStats();
  }, [selectedCenter]);

  // Fetch batches summary when center changes
  useEffect(() => {
    const fetchBatches = async () => {
      if (!selectedCenter) return;
      setBatchesLoading(true);
      try {
        const data = await api.get<BatchSummary[]>(`/api/v1/centers/${selectedCenter.id}/batches-summary`);
        setBatches(data);
      } catch (error) {
        console.error('Failed to fetch batches:', error);
      } finally {
        setBatchesLoading(false);
      }
    };
    fetchBatches();
  }, [selectedCenter]);

  if (!user) {
    return <LoadingState message="Loading..." />;
  }

  const isSuperAdmin = user.role === 'SUPER_ADMIN';

  // Super Admin with no center selected → show center picker
  if (isSuperAdmin && !selectedCenter) {
    return (
      <div className="page-container">
        <PageHeader
          title={`Welcome, ${user.name}`}
          subtitle="Super Admin - Select a center to manage"
        />
        <div className="card card-body mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Select a Center</h2>
          <p className="text-gray-600 mb-6">Choose a center to view its modules and manage operations.</p>
          {centersLoading ? (
            <div className="text-center py-8">
              <div className="spinner mx-auto"></div>
              <p className="mt-2 text-gray-500">Loading centers...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {centers.map((center) => (
                <button
                  key={center.id}
                  onClick={() => setSelectedCenter(center)}
                  className="card card-body hover:ring-2 hover:ring-blue-200 transition text-left"
                >
                  <div className="flex items-center mb-3">
                    <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                      <Building2 className="w-6 h-6 text-blue-600" />
                    </div>
                    <div className="ml-4">
                      <h3 className="font-semibold text-gray-900">{center.name}</h3>
                      <p className="text-sm text-gray-500">{center.city}</p>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600">{center.address}</p>
                  {center.phone && (
                    <p className="text-sm text-blue-600 mt-2">{center.phone}</p>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="card card-body">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Overview - All Centers</h3>
          <p className="text-gray-500 text-sm">Select a center above to see detailed statistics and access modules.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* Header */}
      <PageHeader
        title={selectedCenter?.name || 'Dashboard'}
        subtitle={`${selectedCenter?.city} | ${user.role.replace('_', ' ')}`}
        action={
          isSuperAdmin ? (
            <button
              onClick={() => setSelectedCenter(null)}
              className="btn bg-gray-100 text-gray-600 hover:bg-gray-200 flex items-center gap-2"
              title="Back to center selection"
            >
              <ChevronLeft className="w-4 h-4" />
              All Centers
            </button>
          ) : undefined
        }
      />

      {/* Quick Actions — top priority */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <Link href="/leads?action=create" className="btn-primary flex items-center justify-center py-3">
          <Plus className="w-5 h-5 mr-2" />
          New Enquiry
        </Link>
        <Link href="/attendance" className="btn-success flex items-center justify-center py-3">
          <ClipboardCheck className="w-5 h-5 mr-2" />
          Attendance
        </Link>
        <Link href="/progress" className="btn bg-purple-600 text-white hover:bg-purple-700 flex items-center justify-center py-3">
          <BarChart3 className="w-5 h-5 mr-2" />
          Progress
        </Link>
        <Link href="/renewals" className="btn bg-orange-600 text-white hover:bg-orange-700 flex items-center justify-center py-3">
          <RefreshCw className="w-5 h-5 mr-2" />
          Renewals
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Link href="/leads">
          <StatCard icon={<Users className="w-6 h-6 text-blue-600" />} iconBg="bg-blue-100" label="Leads" value={stats.total_leads} loading={statsLoading} />
        </Link>
        <Link href="/students">
          <StatCard icon={<BookOpen className="w-6 h-6 text-emerald-600" />} iconBg="bg-emerald-100" label="Active Enrolled" value={stats.active_enrollments} loading={statsLoading} />
        </Link>
        <Link href="/attendance">
          <StatCard icon={<Calendar className="w-6 h-6 text-purple-600" />} iconBg="bg-purple-100" label="Today's Classes" value={stats.todays_classes} loading={statsLoading} />
        </Link>
        <Link href="/renewals">
          <StatCard icon={<Clock className="w-6 h-6 text-orange-600" />} iconBg="bg-orange-100" label="Renewals Due" value={stats.pending_renewals} loading={statsLoading} />
        </Link>
      </div>

      {/* Batches Section */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900">Batches</h2>
          <span className="text-sm text-gray-500">{batches.length} active</span>
        </div>

        {batchesLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="card card-body animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-3"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-2/3"></div>
              </div>
            ))}
          </div>
        ) : batches.length === 0 ? (
          <div className="card card-body text-center py-8 text-gray-400 text-sm">
            No active batches found. Create batches in Master Data.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {batches.map((batch) => {
              const timeStr = batch.start_time && batch.end_time
                ? `${formatTime(batch.start_time)} – ${formatTime(batch.end_time)}`
                : batch.start_time ? formatTime(batch.start_time) : null;

              return (
                <Link
                  key={batch.id}
                  href={`/students?batch_id=${batch.id}`}
                  className="card card-body group hover:shadow-md hover:ring-2 hover:ring-blue-200 transition-all cursor-pointer flex flex-col"
                >
                  <div className="flex items-start justify-between mb-1">
                    <h3 className="font-semibold text-gray-900 text-sm leading-tight group-hover:text-blue-700 transition-colors">
                      {batch.name}
                    </h3>
                    <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-blue-500 shrink-0 mt-0.5 transition-colors" />
                  </div>

                  <AgeRange min={batch.age_min} max={batch.age_max} />

                  {batch.days_of_week && batch.days_of_week.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {batch.days_of_week.map(day => (
                        <span key={day} className="text-xs px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded font-medium">
                          {DAY_SHORT[day] || day}
                        </span>
                      ))}
                    </div>
                  )}

                  {timeStr && <p className="text-xs text-gray-500 mt-1">{timeStr}</p>}

                  <div className="mt-auto pt-3 flex items-center justify-between">
                    <span className="text-xs text-gray-500">Active students</span>
                    <span className="text-lg font-bold text-gray-900">{batch.active_students}</span>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>

    </div>
  );
}
