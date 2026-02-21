'use client';

import { ReactNode } from 'react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export default function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="card-static py-16 px-6">
      <div className="text-center max-w-md mx-auto">
        {icon && (
          <div className="mb-4 flex justify-center text-gray-400">
            {icon}
          </div>
        )}

        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          {title}
        </h3>

        {description && (
          <p className="text-sm text-gray-500 mb-6">
            {description}
          </p>
        )}

        {action && (
          <button
            onClick={action.onClick}
            className="btn-primary"
          >
            {action.label}
          </button>
        )}
      </div>
    </div>
  );
}
