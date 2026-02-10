'use client';

import { useState, useEffect, useRef } from 'react';
import Drawer from './ui/Drawer';
import StudentProfileContent from './StudentProfileContent';
import { useStudentLookup } from '@/contexts/StudentLookupContext';
import { useCenter } from '@/contexts/CenterContext';
import { api } from '@/lib/api';

interface SearchResultChild {
  id: number;
  enquiry_id?: string;
  first_name: string;
  last_name?: string;
  dob?: string;
}

interface SearchResultParent {
  id: number;
  name: string;
  phone: string;
  is_primary_contact: boolean;
}

interface SearchResult {
  enrollment_id: number;
  plan_type: string;
  status: string;
  child: SearchResultChild;
  parents: SearchResultParent[];
  batch?: { id: number; name: string };
}

type DrawerView = 'search' | 'profile';

export default function StudentLookupDrawer() {
  const { isLookupOpen, closeLookup } = useStudentLookup();
  const { selectedCenter } = useCenter();

  const [view, setView] = useState<DrawerView>('search');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [selectedChildId, setSelectedChildId] = useState<number | null>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Reset state when drawer opens
  useEffect(() => {
    if (isLookupOpen) {
      setView('search');
      setQuery('');
      setResults([]);
      setSearchError(null);
      setSelectedChildId(null);
      setTimeout(() => searchInputRef.current?.focus(), 300);
    }
  }, [isLookupOpen]);

  // Debounced search
  useEffect(() => {
    if (!query || query.length < 2 || !selectedCenter) {
      setResults([]);
      setSearchError(null);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      setSearchError(null);
      try {
        const data = await api.get<SearchResult[]>(
          `/api/v1/enrollments/students?center_id=${selectedCenter.id}&search=${encodeURIComponent(query)}&limit=20`
        );
        // Deduplicate by child_id (keep first/most recent enrollment)
        const seen = new Set<number>();
        const deduped = data.filter(d => {
          if (seen.has(d.child.id)) return false;
          seen.add(d.child.id);
          return true;
        });
        setResults(deduped);
      } catch (err: any) {
        console.error('Search failed:', err);
        setSearchError(err.message || 'Search failed');
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query, selectedCenter]);

  const handleSelectStudent = (childId: number) => {
    setSelectedChildId(childId);
    setView('profile');
  };

  const handleBack = () => {
    setView('search');
    setSelectedChildId(null);
  };

  const isProfileView = view === 'profile' && selectedChildId != null;
  const drawerTitle = isProfileView ? 'Student Profile' : 'Student Lookup';
  const drawerSize = isProfileView ? 'xl' as const : 'lg' as const;

  return (
    <Drawer
      open={isLookupOpen}
      onClose={closeLookup}
      title={drawerTitle}
      size={drawerSize}
      noPadding={isProfileView}
    >
      {view === 'search' && (
        <div className="flex flex-col">
          {/* Search input */}
          <div className="mb-4">
            <div className="relative">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                ref={searchInputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search by name, parent phone, or enquiry ID..."
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
                autoComplete="off"
              />
              {query && (
                <button
                  onClick={() => { setQuery(''); setResults([]); searchInputRef.current?.focus(); }}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>

          {/* No center selected warning */}
          {!selectedCenter && (
            <div className="text-center py-8 text-amber-600 text-sm">
              Please select a center first
            </div>
          )}

          {/* Error */}
          {searchError && (
            <div className="text-center py-4 text-red-500 text-sm">
              {searchError}
            </div>
          )}

          {/* Loading */}
          {loading && (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-green-600"></div>
              <span className="ml-2 text-sm text-gray-500">Searching...</span>
            </div>
          )}

          {/* No results */}
          {!loading && !searchError && query.length >= 2 && selectedCenter && results.length === 0 && (
            <div className="text-center py-8">
              <svg className="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
              <p className="text-gray-400 text-sm">No students found for &quot;{query}&quot;</p>
            </div>
          )}

          {/* Results list */}
          {!loading && results.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs text-gray-500 mb-2">{results.length} student{results.length !== 1 ? 's' : ''} found</p>
              {results.map((result) => {
                const primaryParent = result.parents.find(p => p.is_primary_contact) || result.parents[0];
                return (
                  <button
                    key={result.child.id}
                    onClick={() => handleSelectStudent(result.child.id)}
                    className="w-full text-left p-3 bg-white rounded-lg hover:bg-green-50 border border-gray-200 hover:border-green-300 transition shadow-sm"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-green-100 text-green-700 rounded-full flex items-center justify-center text-sm font-semibold flex-shrink-0">
                          {result.child.first_name.charAt(0)}
                        </div>
                        <div className="min-w-0">
                          <span className="font-medium text-gray-900">
                            {result.child.first_name} {result.child.last_name || ''}
                          </span>
                          {result.child.enquiry_id && (
                            <span className="ml-2 text-xs text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                              {result.child.enquiry_id}
                            </span>
                          )}
                        </div>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium flex-shrink-0 ${
                        result.status === 'ACTIVE' ? 'bg-green-100 text-green-800' :
                        result.status === 'EXPIRED' ? 'bg-red-100 text-red-800' :
                        result.status === 'PAUSED' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {result.status}
                      </span>
                    </div>
                    <div className="text-sm text-gray-500 mt-1 ml-10">
                      {primaryParent && (
                        <span>{primaryParent.name} &middot; {primaryParent.phone}</span>
                      )}
                      {result.batch && (
                        <span className="ml-2 text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                          {result.batch.name}
                        </span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          )}

          {/* Empty state hint */}
          {!query && selectedCenter && (
            <div className="text-center py-12">
              <svg className="w-16 h-16 text-gray-200 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <p className="text-gray-400 text-sm">Type at least 2 characters to search</p>
              <p className="text-gray-300 text-xs mt-1">Search by student name, parent name, phone, or enquiry ID</p>
            </div>
          )}
        </div>
      )}

      {isProfileView && selectedCenter && (
        <StudentProfileContent
          childId={selectedChildId!}
          centerId={selectedCenter.id}
          onBack={handleBack}
        />
      )}
    </Drawer>
  );
}
