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
