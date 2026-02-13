'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Sidebar from './Sidebar';
import CenterContextBar from './layout/CenterContextBar';
import StudentLookupDrawer from './StudentLookupDrawer';

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthChecked, setIsAuthChecked] = useState(false);

  // Role-based route restrictions
  const roleAllowedPaths: Record<string, string[]> = {
    TRAINER: ['/attendance', '/progress'],
    CENTER_MANAGER: ['/attendance', '/progress', '/students'],
  };

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

    // Restrict roles to allowed modules only
    const userData = localStorage.getItem('user');
    if (userData) {
      const user = JSON.parse(userData);
      const allowedPaths = roleAllowedPaths[user.role];
      if (allowedPaths) {
        const isAllowed = allowedPaths.some(
          p => pathname === p || pathname.startsWith(`${p}/`)
        );
        if (!isAllowed) {
          router.push('/attendance');
          return;
        }
      }
    }

    setIsAuthChecked(true);
  }, [pathname, router]);

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
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <CenterContextBar />
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
      <StudentLookupDrawer />
    </div>
  );
}
