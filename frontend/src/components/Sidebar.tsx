'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useStudentLookup } from '@/contexts/StudentLookupContext';
import {
  Building2, Database, LayoutDashboard, Users, GraduationCap, ClipboardCheck,
  CalendarCheck, TrendingUp, FileText, RefreshCw, Settings,
  Upload, Search, LogOut,
} from 'lucide-react';

interface User {
  id: number;
  name: string;
  email: string;
  role: string;
  center_id: number | null;
}

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const { openLookup } = useStudentLookup();

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
  }, []);

  // Ctrl+K / Cmd+K keyboard shortcut to open student lookup
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        openLookup();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [openLookup]);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    router.push('/login');
  };

  const menuItems = [
    { name: 'Centers', href: '/centers', icon: Building2, roles: ['SUPER_ADMIN'] },
    { name: 'Master Data', href: '/mdm', icon: Database, roles: ['SUPER_ADMIN', 'CENTER_ADMIN'] },
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, roles: ['SUPER_ADMIN', 'CENTER_ADMIN', 'COUNSELOR'] },
    { name: 'Leads', href: '/leads', icon: Users, roles: ['SUPER_ADMIN', 'CENTER_ADMIN', 'COUNSELOR'] },
    { name: 'Students', href: '/students', icon: GraduationCap, roles: ['SUPER_ADMIN', 'CENTER_ADMIN', 'COUNSELOR'] },
    { name: 'Enrollments', href: '/enrollments', icon: ClipboardCheck, roles: ['SUPER_ADMIN', 'CENTER_ADMIN', 'COUNSELOR'] },
    { name: 'Attendance', href: '/attendance', icon: CalendarCheck, roles: ['SUPER_ADMIN', 'CENTER_ADMIN', 'CENTER_MANAGER', 'TRAINER'] },
    { name: 'Progress', href: '/progress', icon: TrendingUp, roles: ['SUPER_ADMIN', 'CENTER_ADMIN', 'CENTER_MANAGER', 'TRAINER'] },
    { name: 'Report Cards', href: '/report-cards', icon: FileText, roles: ['SUPER_ADMIN', 'CENTER_ADMIN'] },
    { name: 'Renewals', href: '/renewals', icon: RefreshCw, roles: ['SUPER_ADMIN', 'CENTER_ADMIN', 'COUNSELOR'] },
    { name: 'Admin', href: '/admin', icon: Settings, roles: ['SUPER_ADMIN', 'CENTER_ADMIN'] },
    { name: 'Import Data', href: '/import', icon: Upload, roles: ['SUPER_ADMIN', 'CENTER_ADMIN'] },
  ];

  const filteredMenuItems = menuItems.filter(item =>
    user && item.roles.includes(user.role)
  );

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-gray-900 to-gray-950 text-white w-60">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-white/10">
        <h1 className="text-lg font-bold tracking-tight">Little Gym CRM</h1>
        {user && (
          <p className="text-xs text-gray-400 mt-1 font-medium">{user.role.replace(/_/g, ' ')}</p>
        )}
      </div>

      {/* Student Search */}
      <div className="px-3 py-3">
        <button
          onClick={openLookup}
          className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-gray-400 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 hover:text-white transition-colors"
        >
          <Search className="w-4 h-4" />
          <span className="text-xs">Search students...</span>
          <kbd className="ml-auto text-[10px] text-gray-500 bg-white/10 px-1.5 py-0.5 rounded font-mono">Ctrl+K</kbd>
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-2 px-2">
        {filteredMenuItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 text-sm font-medium rounded-lg my-0.5 transition-colors ${
                isActive
                  ? 'bg-white/10 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Icon className="w-[18px] h-[18px] flex-shrink-0" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* User Info & Logout */}
      {user && (
        <div className="p-4 border-t border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
              {user.name.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user.name}</p>
              <p className="text-xs text-gray-500 truncate">{user.email}</p>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 text-gray-500 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
