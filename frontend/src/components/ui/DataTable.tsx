'use client';

import { ReactNode, useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react';

export interface Column<T> {
  key: string;
  label: string;
  render?: (row: T) => ReactNode;
  className?: string;
  sortable?: boolean;
  sortKey?: string; // Custom key for sorting if different from display key
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  loading?: boolean;
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
  searchable?: boolean;
  searchPlaceholder?: string;
  defaultSortKey?: string;
  defaultSortDirection?: 'asc' | 'desc';
}

export default function DataTable<T extends { id: number | string }>({
  data,
  columns,
  loading,
  onRowClick,
  emptyMessage = 'No data available',
  searchable = false,
  searchPlaceholder = 'Search...',
  defaultSortKey,
  defaultSortDirection = 'asc',
}: DataTableProps<T>) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortKey, setSortKey] = useState<string | null>(defaultSortKey || null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>(defaultSortDirection);

  // Handle column sort
  const handleSort = (column: Column<T>) => {
    if (!column.sortable) return;

    const key = column.sortKey || column.key;
    if (sortKey === key) {
      // Toggle direction
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // New column
      setSortKey(key);
      setSortDirection('asc');
    }
  };

  // Filter and sort data
  const processedData = useMemo(() => {
    let filtered = [...data];

    // Search filter
    if (searchable && searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter((row) => {
        return columns.some((col) => {
          const value = (row as any)[col.key];
          return value?.toString().toLowerCase().includes(query);
        });
      });
    }

    // Sort
    if (sortKey) {
      filtered.sort((a, b) => {
        const aVal = (a as any)[sortKey];
        const bVal = (b as any)[sortKey];

        // Handle null/undefined
        if (aVal == null && bVal == null) return 0;
        if (aVal == null) return 1;
        if (bVal == null) return -1;

        // Compare values
        let comparison = 0;
        if (typeof aVal === 'string' && typeof bVal === 'string') {
          comparison = aVal.localeCompare(bVal);
        } else if (typeof aVal === 'number' && typeof bVal === 'number') {
          comparison = aVal - bVal;
        } else {
          comparison = String(aVal).localeCompare(String(bVal));
        }

        return sortDirection === 'asc' ? comparison : -comparison;
      });
    }

    return filtered;
  }, [data, searchQuery, sortKey, sortDirection, columns, searchable]);

  if (loading) {
    return (
      <div className="table-wrapper">
        <div className="p-8 space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex gap-4">
              <div className="skeleton h-4 w-1/4" />
              <div className="skeleton h-4 w-1/3" />
              <div className="skeleton h-4 w-1/5" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="table-wrapper">
      {/* Search bar */}
      {searchable && (
        <div className="p-4 border-b border-gray-200">
          <input
            type="text"
            placeholder={searchPlaceholder}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input w-full"
          />
        </div>
      )}

      {processedData.length === 0 ? (
        <div className="p-12 text-center text-gray-500 text-sm">
          {searchQuery ? `No results found for "${searchQuery}"` : emptyMessage}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th
                    key={column.key}
                    onClick={() => handleSort(column)}
                    className={`table-header-cell ${column.sortable ? 'cursor-pointer select-none hover:bg-gray-100' : ''} ${column.className || ''}`}
                  >
                    <div className="flex items-center gap-2">
                      <span>{column.label}</span>
                      {column.sortable && (
                        <span className="text-gray-400">
                          {sortKey === (column.sortKey || column.key) ? (
                            sortDirection === 'asc' ? (
                              <ChevronUp className="w-4 h-4" />
                            ) : (
                              <ChevronDown className="w-4 h-4" />
                            )
                          ) : (
                            <ChevronsUpDown className="w-4 h-4 opacity-50" />
                          )}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {processedData.map((row) => (
                <tr
                  key={row.id}
                  onClick={() => onRowClick?.(row)}
                  className={`table-row ${onRowClick ? 'cursor-pointer' : ''}`}
                >
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={`table-cell whitespace-nowrap ${column.className || ''}`}
                    >
                      {column.render ? column.render(row) : (row as any)[column.key]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
