'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Sidebar from './Sidebar';
import CenterContextBar from './layout/CenterContextBar';
import StudentLookupDrawer from './StudentLookupDrawer';
import { usePermissions } from '@/contexts/PermissionsContext';
import { Menu } from 'lucide-react';

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthChecked, setIsAuthChecked] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);       // mobile overlay
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false); // desktop icon-only
  const { permissions, loading: permLoading } = usePermissions();

  // Map routes to permission keys for configurable roles
  const routePermissionMap: Record<string, string> = {
    '/dashboard': 'module:dashboard',
    '/leads': 'module:leads',
    '/students': 'module:students',
    '/enrollments': 'module:enrollments',
    '/attendance': 'module:attendance',
    '/progress': 'module:progress',
    '/report-cards': 'module:report_cards',
    '/renewals': 'module:renewals',
    '/import': 'action:import_data',
  };

  // Roles that use configurable permissions (not hardcoded)
  const configurableRoles = ['CENTER_MANAGER', 'TRAINER', 'COUNSELOR'];

  useEffect(() => {
    // Skip auth check for login page and home page
    if (pathname === '/login' || pathname === '/') {
      setIsAuthChecked(true);
      return;
    }

    // Check if user is authenticated
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }

    // Wait for permissions to load before checking access
    if (permLoading) return;

    const userData = localStorage.getItem('user');
    if (userData) {
      const user = JSON.parse(userData);

      // SUPER_ADMIN and CENTER_ADMIN have unrestricted access
      if (user.role === 'SUPER_ADMIN' || user.role === 'CENTER_ADMIN') {
        setIsAuthChecked(true);
        return;
      }

      // For configurable roles, check permissions from the database
      if (configurableRoles.includes(user.role)) {
        // Find which permission key matches the current route
        const matchedRoute = Object.keys(routePermissionMap).find(
          route => pathname === route || pathname.startsWith(`${route}/`)
        );

        if (matchedRoute) {
          const permKey = routePermissionMap[matchedRoute];
          if (!permissions[permKey]) {
            // Find the first allowed route to redirect to
            const firstAllowed = Object.entries(routePermissionMap).find(
              ([, pk]) => permissions[pk]
            );
            router.push(firstAllowed ? firstAllowed[0] : '/login');
            return;
          }
        }
      }
    }

    setIsAuthChecked(true);
  }, [pathname, router, permissions, permLoading]);

  // Close sidebar when navigating on mobile (must be before early returns)
  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  // Don't show sidebar on login page or home page
  if (pathname === '/login' || pathname === '/') {
    return <>{children}</>;
  }

  // Show loading state while checking auth
  if (!isAuthChecked) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar — mobile: slide overlay, desktop: inline with collapse */}
      <div className={`
        fixed inset-y-0 left-0 z-40
        lg:relative lg:z-auto lg:flex lg:flex-col lg:shrink-0
        transition-all duration-200 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        ${sidebarCollapsed ? 'lg:w-16' : 'lg:w-60'}
      `}>
        <Sidebar
          onClose={() => setSidebarOpen(false)}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(c => !c)}
        />
      </div>

      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        {/* Mobile top bar with hamburger */}
        <div className="flex items-center lg:hidden bg-white border-b border-gray-200 px-3 py-2 gap-2 shrink-0">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
          >
            <Menu className="w-5 h-5" />
          </button>
          <span className="font-semibold text-gray-900 text-sm">Little Gym CRM</span>
        </div>
        <CenterContextBar />
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
      <StudentLookupDrawer />
    </div>
  );
}
