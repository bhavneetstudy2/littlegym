'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useCenter } from '@/contexts/CenterContext';
import { api } from '@/lib/api';
import { Users, BookOpen, Calendar, Clock, Plus, ClipboardCheck, BarChart3, RefreshCw, ChevronLeft, Building2 } from 'lucide-react';
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

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (!userData) {
      router.push('/login');
      return;
    }
    setUser(JSON.parse(userData));
  }, [router]);

  // Fetch stats when center changes - single optimized API call
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

  if (!user) {
    return <LoadingState message="Loading..." />;
  }

  const isSuperAdmin = user.role === 'SUPER_ADMIN';

  // If Super Admin and no center selected, show center selection
  if (isSuperAdmin && !selectedCenter) {
    return (
      <div className="page-container">
        <PageHeader
          title={`Welcome, ${user.name}`}
          subtitle="Super Admin - Select a center to manage"
        />

        {/* Center Selection */}
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

        {/* Quick Stats Across All Centers */}
        <div className="card card-body">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Overview - All Centers</h3>
          <p className="text-gray-500 text-sm">Select a center above to see detailed statistics and access modules.</p>
        </div>
      </div>
    );
  }

  // Center is selected - show modules and dashboard
  return (
    <div className="page-container">
      {/* Header with Center Info */}
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

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard
          icon={<Users className="w-6 h-6 text-blue-600" />}
          iconBg="bg-blue-100"
          label="Leads"
          value={stats.total_leads}
          loading={statsLoading}
        />
        <StatCard
          icon={<BookOpen className="w-6 h-6 text-emerald-600" />}
          iconBg="bg-emerald-100"
          label="Enrolled"
          value={stats.active_enrollments}
          loading={statsLoading}
        />
        <StatCard
          icon={<Calendar className="w-6 h-6 text-purple-600" />}
          iconBg="bg-purple-100"
          label="Today's Classes"
          value={stats.todays_classes}
          loading={statsLoading}
        />
        <StatCard
          icon={<Clock className="w-6 h-6 text-orange-600" />}
          iconBg="bg-orange-100"
          label="Renewals Due"
          value={stats.pending_renewals}
          loading={statsLoading}
        />
      </div>

      {/* Main Modules */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Lead Lifecycle Module */}
        <Link href="/leads" className="block">
          <div className="card card-body border-t-4 border-blue-500 hover:shadow-lg transition">
            <div className="flex items-center mb-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Users className="w-8 h-8 text-blue-600" />
              </div>
              <div className="ml-4">
                <h3 className="text-xl font-bold text-gray-900">Lead Lifecycle</h3>
                <p className="text-gray-500">Enquiry to Enrollment</p>
              </div>
            </div>
            <p className="text-gray-600 mb-4">
              Manage the complete lead journey from initial enquiry, intro visits, follow-ups, to final conversion.
            </p>
            <div className="flex flex-wrap gap-2">
              <span className="badge-blue">Discovery</span>
              <span className="badge-blue">Intro Visits</span>
              <span className="badge-blue">Follow-ups</span>
              <span className="badge-blue">Conversion</span>
            </div>
          </div>
        </Link>

        {/* Enrolled Students Module */}
        <Link href="/students" className="block">
          <div className="card card-body border-t-4 border-green-500 hover:shadow-lg transition">
            <div className="flex items-center mb-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <BookOpen className="w-8 h-8 text-green-600" />
              </div>
              <div className="ml-4">
                <h3 className="text-xl font-bold text-gray-900">Enrolled Students</h3>
                <p className="text-gray-500">Student Management</p>
              </div>
            </div>
            <p className="text-gray-600 mb-4">
              View enrolled students, mark attendance, track skill progress, and generate report cards.
            </p>
            <div className="flex flex-wrap gap-2">
              <span className="badge-green">Students</span>
              <span className="badge-green">Attendance</span>
              <span className="badge-green">Progress</span>
              <span className="badge-green">Reports</span>
            </div>
          </div>
        </Link>
      </div>

      {/* Quick Actions */}
      <div className="card card-body">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Link
            href="/leads?action=create"
            className="btn-primary flex items-center justify-center"
          >
            <Plus className="w-5 h-5 mr-2" />
            New Lead
          </Link>
          <Link
            href="/students"
            className="btn-success flex items-center justify-center"
          >
            <ClipboardCheck className="w-5 h-5 mr-2" />
            Attendance
          </Link>
          <Link
            href="/students"
            className="btn bg-purple-600 text-white hover:bg-purple-700 flex items-center justify-center"
          >
            <BarChart3 className="w-5 h-5 mr-2" />
            Progress
          </Link>
          <Link
            href="/renewals"
            className="btn bg-orange-600 text-white hover:bg-orange-700 flex items-center justify-center"
          >
            <RefreshCw className="w-5 h-5 mr-2" />
            Renewals
          </Link>
        </div>
      </div>
    </div>
  );
}
