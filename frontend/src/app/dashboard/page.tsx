'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface User {
  id: number;
  name: string;
  email: string;
  role: string;
  center_id: number | null;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user');

    if (!token || !userData) {
      router.push('/login');
      return;
    }

    setUser(JSON.parse(userData));
    setLoading(false);
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    router.push('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">
                The Little Gym CRM
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">{user.name}</span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Welcome Card */}
          <div className="bg-white rounded-lg shadow px-6 py-8 mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Welcome back, {user.name}!
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-sm text-blue-600 font-medium">Email</p>
                <p className="text-lg font-semibold text-gray-900">{user.email}</p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <p className="text-sm text-green-600 font-medium">Role</p>
                <p className="text-lg font-semibold text-gray-900">{user.role.replace('_', ' ')}</p>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <p className="text-sm text-purple-600 font-medium">Center ID</p>
                <p className="text-lg font-semibold text-gray-900">
                  {user.center_id || 'All Centers (Super Admin)'}
                </p>
              </div>
            </div>
          </div>

          {/* Phase 2 Complete Notice */}
          <div className="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 rounded-lg mb-6">
            <p className="font-bold">🎉 Phase 2 Complete - Authentication Working!</p>
            <p className="mt-2">
              You have successfully logged in with JWT authentication. The backend API validated
              your credentials and returned your user profile.
            </p>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Total Leads</dt>
                      <dd className="text-lg font-semibold text-gray-900">Coming Soon</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Active Enrollments</dt>
                      <dd className="text-lg font-semibold text-gray-900">Coming Soon</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Today's Classes</dt>
                      <dd className="text-lg font-semibold text-gray-900">Coming Soon</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Pending Renewals</dt>
                      <dd className="text-lg font-semibold text-gray-900">Coming Soon</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Next Steps */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Next Development Phases</h3>
            <ul className="space-y-3">
              <li className="flex items-start">
                <span className="text-green-500 mr-2">✓</span>
                <span className="text-gray-700">Phase 1: Project Setup - Complete</span>
              </li>
              <li className="flex items-start">
                <span className="text-green-500 mr-2">✓</span>
                <span className="text-gray-700">Phase 2: Auth + Users + RBAC - Complete</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-500 mr-2">→</span>
                <span className="text-gray-700">Phase 3: Leads + Discovery + Intro Visits</span>
              </li>
              <li className="flex items-start">
                <span className="text-gray-400 mr-2">○</span>
                <span className="text-gray-500">Phase 4: Enrollment + Payments + Discounts</span>
              </li>
              <li className="flex items-start">
                <span className="text-gray-400 mr-2">○</span>
                <span className="text-gray-500">Phase 5: Batches + Sessions + Attendance</span>
              </li>
              <li className="flex items-start">
                <span className="text-gray-400 mr-2">○</span>
                <span className="text-gray-500">Phase 6: Curriculum + Skills + Progress</span>
              </li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}
