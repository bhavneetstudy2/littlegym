'use client';

import { useCenterContext } from '@/hooks/useCenterContext';
import { useRouter } from 'next/navigation';
import { MapPin, X } from 'lucide-react';

export default function CenterContextBar() {
  const { selectedCenter, setSelectedCenter, centers, isSuperAdmin } = useCenterContext();
  const router = useRouter();

  if (!selectedCenter) return null;

  return (
    <div className="bg-blue-50/80 border-b border-blue-100 px-6 py-2.5 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <MapPin className="w-4 h-4 text-blue-500" />
        <span className="text-xs text-gray-500 font-medium">
          {isSuperAdmin ? 'Viewing:' : 'Your Center:'}
        </span>
        <span className="text-sm font-semibold text-gray-900">{selectedCenter.name}</span>
        {selectedCenter.city && (
          <span className="text-xs text-gray-400">({selectedCenter.city})</span>
        )}
      </div>

      {isSuperAdmin && (
        <div className="flex items-center gap-2">
          <select
            value={selectedCenter.id}
            onChange={(e) => {
              const centerId = parseInt(e.target.value);
              const center = centers.find(c => c.id === centerId);
              if (center) setSelectedCenter(center);
            }}
            className="px-3 py-1.5 text-xs border border-gray-200 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          >
            {centers.map(center => (
              <option key={center.id} value={center.id}>
                {center.name} {center.city ? `(${center.city})` : ''}
              </option>
            ))}
          </select>

          <button
            onClick={() => {
              setSelectedCenter(null);
              router.push('/centers');
            }}
            className="btn-ghost btn-sm gap-1"
          >
            <X className="w-3.5 h-3.5" />
            Exit
          </button>
        </div>
      )}
    </div>
  );
}
