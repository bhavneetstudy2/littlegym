import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  return name.slice(0, 2).toUpperCase();
}

const AVATAR_COLORS = [
  'bg-violet-600', 'bg-emerald-600', 'bg-blue-600', 'bg-amber-600',
  'bg-rose-600', 'bg-cyan-600', 'bg-indigo-600', 'bg-teal-600',
  'bg-orange-600', 'bg-pink-600', 'bg-lime-700', 'bg-fuchsia-600',
];

export function getAvatarColor(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '-';
  try {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

export function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '-';
  try {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
}

const STATUS_BADGE_MAP: Record<string, string> = {
  // Enrollment statuses
  ACTIVE: 'badge-green',
  EXPIRED: 'badge-red',
  CANCELLED: 'badge-gray',
  PAUSED: 'badge-yellow',
  // Lead statuses
  ENQUIRY_RECEIVED: 'badge-blue',
  DISCOVERY_COMPLETED: 'badge-blue',
  IV_SCHEDULED: 'badge-purple',
  IV_COMPLETED: 'badge-green',
  IV_NO_SHOW: 'badge-red',
  FOLLOW_UP_PENDING: 'badge-yellow',
  CONVERTED: 'badge-green',
  CLOSED_LOST: 'badge-gray',
  // Attendance
  PRESENT: 'badge-green',
  ABSENT: 'badge-red',
  MAKEUP: 'badge-purple',
  TRIAL: 'badge-blue',
  // Skill levels
  NOT_STARTED: 'badge-gray',
  IN_PROGRESS: 'badge-blue',
  ACHIEVED: 'badge-green',
  MASTERED: 'badge-purple',
  // User roles
  SUPER_ADMIN: 'badge-purple',
  CENTER_ADMIN: 'badge-blue',
  TRAINER: 'badge-green',
  COUNSELOR: 'badge-orange',
  CENTER_MANAGER: 'badge-blue',
};

export function getStatusBadgeClass(status: string): string {
  return STATUS_BADGE_MAP[status] || 'badge-gray';
}

export function formatStatus(status: string): string {
  return status.replace(/_/g, ' ');
}
