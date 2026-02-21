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

/**
 * Format date as dd/mm/yyyy
 * @param dateStr - Date string in any format (ISO, yyyy-mm-dd, etc.)
 * @returns Date in dd/mm/yyyy format or '-' if invalid
 */
export function formatDateDDMMYYYY(dateStr: string | null | undefined): string {
  if (!dateStr) return '-';
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return '-';

    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();

    return `${day}/${month}/${year}`;
  } catch {
    return '-';
  }
}

/**
 * Convert dd/mm/yyyy to yyyy-mm-dd (for API)
 * @param ddmmyyyy - Date in dd/mm/yyyy format
 * @returns Date in yyyy-mm-dd format or empty string if invalid
 */
export function convertDDMMYYYYtoISO(ddmmyyyy: string): string {
  if (!ddmmyyyy) return '';

  const parts = ddmmyyyy.split('/');
  if (parts.length !== 3) return '';

  const [day, month, year] = parts;

  // Validate
  const dayNum = parseInt(day, 10);
  const monthNum = parseInt(month, 10);
  const yearNum = parseInt(year, 10);

  if (dayNum < 1 || dayNum > 31) return '';
  if (monthNum < 1 || monthNum > 12) return '';
  if (yearNum < 1900 || yearNum > 2100) return '';

  return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
}

/**
 * Convert yyyy-mm-dd to dd/mm/yyyy (for display)
 * @param isoDate - Date in yyyy-mm-dd format
 * @returns Date in dd/mm/yyyy format
 */
export function convertISOtoDDMMYYYY(isoDate: string): string {
  if (!isoDate) return '';

  const parts = isoDate.split('-');
  if (parts.length !== 3) return '';

  const [year, month, day] = parts;
  return `${day}/${month}/${year}`;
}

/**
 * Get today's date in dd/mm/yyyy format
 */
export function getTodayDDMMYYYY(): string {
  const today = new Date();
  const day = String(today.getDate()).padStart(2, '0');
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const year = today.getFullYear();
  return `${day}/${month}/${year}`;
}

/**
 * Get today's date in yyyy-mm-dd format (for API)
 */
export function getTodayISO(): string {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}
