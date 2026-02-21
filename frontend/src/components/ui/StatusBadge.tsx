'use client';

import { getStatusBadgeClass, formatStatus } from '@/lib/utils';

interface StatusBadgeProps {
  status: string;
  label?: string;
}

export default function StatusBadge({ status, label }: StatusBadgeProps) {
  return (
    <span className={getStatusBadgeClass(status)}>
      {label || formatStatus(status)}
    </span>
  );
}
