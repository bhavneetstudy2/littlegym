'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useStudentLookup } from '@/contexts/StudentLookupContext';
import { usePermissions } from '@/contexts/PermissionsContext';
import {
  Building2, Database, LayoutDashboard, Users, GraduationCap, ClipboardCheck,
  CalendarCheck, TrendingUp, FileText, RefreshCw, Settings,
  Upload, Search, LogOut, ChevronLeft, ChevronRight, Tent,
} from 'lucide-react';

interface User {
  id: number;
  name: string;
  email: string;
  role: string;
  center_id: number | null;
}

interface SidebarProps {
  onClose?: () => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export default function Sidebar({ onClose, collapsed = false, onToggleCollapse }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const { openLookup } = useStudentLookup();
  const { hasPermission } = usePermissions();

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

  // permissionKey maps sidebar items to configurable permission keys
  const menuItems = [
    { name: 'Centers', href: '/centers', icon: Building2, roles: ['SUPER_ADMIN'], permissionKey: null },
    { name: 'Master Data', href: '/mdm', icon: Database, roles: ['SUPER_ADMIN', 'CENTER_ADMIN'], permissionKey: null },
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, roles: ['SUPER_ADMIN', 'CENTER_ADMIN'], permissionKey: 'module:dashboard' },
    { name: 'Leads', href: '/leads', icon: Users, roles: ['SUPER_ADMIN', 'CENTER_ADMIN'], permissionKey: 'module:leads' },
    { name: 'Students', href: '/students', icon: GraduationCap, roles: ['SUPER_ADMIN', 'CENTER_ADMIN'], permissionKey: 'module:students' },
    { name: 'Enrollments', href: '/enrollments', icon: ClipboardCheck, roles: ['SUPER_ADMIN', 'CENTER_ADMIN'], permissionKey: 'module:enrollments' },
    { name: 'Attendance', href: '/attendance', icon: CalendarCheck, roles: ['SUPER_ADMIN', 'CENTER_ADMIN'], permissionKey: 'module:attendance' },
    { name: 'Progress', href: '/progress', icon: TrendingUp, roles: ['SUPER_ADMIN', 'CENTER_ADMIN'], permissionKey: 'module:progress' },
    { name: 'Camps', href: '/camps', icon: Tent, roles: ['SUPER_ADMIN', 'CENTER_ADMIN', 'CENTER_MANAGER'], permissionKey: null },
    { name: 'Report Cards', href: '/report-cards', icon: FileText, roles: ['SUPER_ADMIN', 'CENTER_ADMIN'], permissionKey: 'module:report_cards' },
    { name: 'Renewals', href: '/renewals', icon: RefreshCw, roles: ['SUPER_ADMIN', 'CENTER_ADMIN'], permissionKey: 'module:renewals' },
    { name: 'Admin', href: '/admin', icon: Settings, roles: ['SUPER_ADMIN', 'CENTER_ADMIN'], permissionKey: null },
    { name: 'Import Data', href: '/import', icon: Upload, roles: ['SUPER_ADMIN', 'CENTER_ADMIN'], permissionKey: 'action:import_data' },
  ];

  const filteredMenuItems = menuItems.filter(item => {
    if (!user) return false;
    // SUPER_ADMIN and CENTER_ADMIN: use hardcoded roles list (always full access)
    if (item.roles.includes(user.role)) return true;
    // For other roles (CENTER_MANAGER, TRAINER, COUNSELOR): check configurable permissions
    if (item.permissionKey && hasPermission(item.permissionKey)) return true;
    return false;
  });

  return (
    <div className={`flex flex-col h-full bg-gradient-to-b from-gray-900 to-gray-950 text-white overflow-hidden transition-all duration-200 ${collapsed ? 'w-16' : 'w-60'}`}>
      {/* Logo + collapse toggle */}
      <div className={`flex items-center border-b border-white/10 shrink-0 ${collapsed ? 'justify-center py-4 px-2' : 'px-4 py-4 gap-2'}`}>
        {!collapsed && <h1 className="text-base font-bold tracking-tight flex-1 truncate">Little Gym CRM</h1>}
        {/* Collapse toggle — desktop only */}
        <button
          onClick={onToggleCollapse}
          className="hidden lg:flex p-1.5 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors shrink-0"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Student Search */}
      <div className={`py-2 shrink-0 ${collapsed ? 'px-2' : 'px-3'}`}>
        <button
          onClick={openLookup}
          title="Search students (Ctrl+K)"
          className={`w-full flex items-center text-gray-400 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 hover:text-white transition-colors ${collapsed ? 'justify-center p-2' : 'gap-2 px-3 py-2'}`}
        >
          <Search className="w-4 h-4 shrink-0" />
          {!collapsed && (
            <>
              <span className="text-xs flex-1 text-left">Search students...</span>
              <kbd className="text-[10px] text-gray-500 bg-white/10 px-1.5 py-0.5 rounded font-mono">Ctrl+K</kbd>
            </>
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className={`flex-1 overflow-y-auto py-1 ${collapsed ? 'px-2' : 'px-2'}`}>
        {filteredMenuItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onClose}
              title={collapsed ? item.name : undefined}
              className={`flex items-center rounded-lg my-0.5 transition-colors ${
                collapsed ? 'justify-center p-2.5' : 'gap-3 px-3 py-2.5'
              } ${
                isActive ? 'bg-white/10 text-white' : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Icon className="w-[18px] h-[18px] shrink-0" />
              {!collapsed && <span className="text-sm font-medium">{item.name}</span>}
            </Link>
          );
        })}
      </nav>

      {/* User Info & Logout */}
      {user && (
        <div className={`border-t border-white/10 shrink-0 ${collapsed ? 'p-2' : 'p-3'}`}>
          <div className={`flex items-center ${collapsed ? 'flex-col gap-2' : 'gap-2'}`}>
            <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-xs font-bold text-white shrink-0">
              {user.name.charAt(0).toUpperCase()}
            </div>
            {!collapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate leading-tight">{user.name}</p>
                <p className="text-xs text-gray-500 truncate">{user.email}</p>
              </div>
            )}
            <button
              onClick={handleLogout}
              className="p-1.5 text-gray-500 hover:text-white hover:bg-white/10 rounded-lg transition-colors shrink-0"
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
