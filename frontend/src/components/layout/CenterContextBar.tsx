'use client';

import { useCenterContext } from '@/hooks/useCenterContext';
import { useRouter } from 'next/navigation';

export default function CenterContextBar() {
  const { selectedCenter, setSelectedCenter, centers, isSuperAdmin } = useCenterContext();
  const router = useRouter();

  // Don't show if no center is selected
  if (!selectedCenter) return null;

  return (
    <div className="bg-blue-50 border-b border-blue-200 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className="text-xl" role="img" aria-label="location">
          📍
        </span>
        <span className="text-sm text-gray-600">
          {isSuperAdmin ? 'Viewing:' : 'Your Center:'}
        </span>
        <span className="font-semibold text-gray-900">{selectedCenter.name}</span>
        {selectedCenter.city && (
          <span className="text-sm text-gray-500">({selectedCenter.city})</span>
        )}
      </div>

      {isSuperAdmin && (
        <div className="flex items-center gap-3">
          {/* Switch Center Dropdown */}
          <select
            value={selectedCenter.id}
            onChange={(e) => {
              const centerId = parseInt(e.target.value);
              const center = centers.find(c => c.id === centerId);
              if (center) {
                setSelectedCenter(center);
              }
            }}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {centers.map(center => (
              <option key={center.id} value={center.id}>
                {center.name} {center.city ? `(${center.city})` : ''}
              </option>
            ))}
          </select>

          {/* Exit Button */}
          <button
            onClick={() => {
              setSelectedCenter(null);
              router.push('/centers');
            }}
            className="px-3 py-1.5 text-sm text-gray-700 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50 transition font-medium"
          >
            Exit
          </button>
        </div>
      )}
    </div>
  );
}
