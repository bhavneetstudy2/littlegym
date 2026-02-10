'use client';

import { useRouter } from 'next/navigation';
import { useCenterContext } from '@/hooks/useCenterContext';

interface MDMCard {
  title: string;
  description: string;
  icon: string;
  href: string;
  scope: 'global' | 'center';
  requiresSuperAdmin?: boolean;
}

const mdmCards: MDMCard[] = [
  // Global Master Data (Super Admin only)
  {
    title: 'Class Types',
    description: 'Manage global class types (Birds, Bugs, Beasts, etc.)',
    icon: '🎯',
    href: '/mdm/global/class-types',
    scope: 'global',
    requiresSuperAdmin: true,
  },
  {
    title: 'Curricula',
    description: 'Manage global curriculum templates and skills',
    icon: '📚',
    href: '/mdm/global/curricula',
    scope: 'global',
    requiresSuperAdmin: true,
  },
  {
    title: 'Skills',
    description: 'Manage global skills library',
    icon: '⭐',
    href: '/mdm/global/skills',
    scope: 'global',
    requiresSuperAdmin: true,
  },
  // Center-specific Master Data
  {
    title: 'Batches',
    description: 'Manage center-specific batches and schedules',
    icon: '📅',
    href: '/mdm/center/batches',
    scope: 'center',
  },
  {
    title: 'Users',
    description: 'Manage center staff and permissions',
    icon: '👥',
    href: '/mdm/center/users',
    scope: 'center',
  },
];

export default function MDMPage() {
  const router = useRouter();
  const { selectedCenter, isSuperAdmin } = useCenterContext();

  const globalCards = mdmCards.filter((c) => c.scope === 'global');
  const centerCards = mdmCards.filter((c) => c.scope === 'center');

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Master Data Management</h1>
          <p className="text-gray-600">
            Manage global and center-specific master data for your organization
          </p>
        </div>

        {/* Global Master Data */}
        {isSuperAdmin && (
          <div className="mb-12">
            <div className="flex items-center gap-2 mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Global Master Data</h2>
              <span className="px-2.5 py-1 bg-purple-100 text-purple-800 text-xs font-medium rounded">
                Super Admin Only
              </span>
            </div>
            <p className="text-sm text-gray-600 mb-6">
              These settings apply across all centers in the organization
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {globalCards.map((card) => (
                <button
                  key={card.href}
                  onClick={() => router.push(card.href)}
                  className="bg-white rounded-xl shadow-sm border-2 border-gray-200 p-6 hover:border-purple-500 hover:shadow-md transition text-left"
                >
                  <div className="text-4xl mb-3">{card.icon}</div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{card.title}</h3>
                  <p className="text-sm text-gray-600">{card.description}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Center-Specific Master Data */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Center Master Data</h2>
            {selectedCenter && (
              <span className="px-2.5 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                {selectedCenter.name}
              </span>
            )}
          </div>
          {!selectedCenter ? (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
              <div className="flex items-start gap-3">
                <span className="text-2xl">⚠️</span>
                <div>
                  <h3 className="font-semibold text-yellow-900 mb-1">No Center Selected</h3>
                  <p className="text-sm text-yellow-800 mb-3">
                    Please select a center to manage center-specific master data
                  </p>
                  {isSuperAdmin && (
                    <button
                      onClick={() => router.push('/centers')}
                      className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition text-sm font-medium"
                    >
                      Select Center
                    </button>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <>
              <p className="text-sm text-gray-600 mb-6">
                These settings apply only to the selected center
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {centerCards.map((card) => (
                  <button
                    key={card.href}
                    onClick={() => router.push(card.href)}
                    className="bg-white rounded-xl shadow-sm border-2 border-gray-200 p-6 hover:border-blue-500 hover:shadow-md transition text-left"
                  >
                    <div className="text-4xl mb-3">{card.icon}</div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{card.title}</h3>
                    <p className="text-sm text-gray-600">{card.description}</p>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
