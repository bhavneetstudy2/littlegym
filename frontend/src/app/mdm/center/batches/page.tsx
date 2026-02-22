'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useCenter } from '@/contexts/CenterContext';
import DataTable, { Column } from '@/components/ui/DataTable';
import Drawer from '@/components/ui/Drawer';
import EmptyState from '@/components/ui/EmptyState';

interface Batch {
  id: number;
  name: string;
  center_id: number;
  age_min?: number;
  age_max?: number;
  days_of_week?: string[];
  start_time?: string;
  end_time?: string;
  capacity?: number;
  active: boolean;
  created_at: string;
  updated_at: string;
}

interface BatchFormData {
  name: string;
  age_min: string;
  age_max: string;
  days_of_week: string[];
  start_time: string;
  end_time: string;
  capacity: string;
  active: boolean;
}

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export default function BatchesPage() {
  const router = useRouter();
  const { selectedCenter } = useCenter();
  const [batches, setBatches] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(true);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingBatch, setEditingBatch] = useState<Batch | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [showInactive, setShowInactive] = useState(false);

  const [formData, setFormData] = useState<BatchFormData>({
    name: '',
    age_min: '',
    age_max: '',
    days_of_week: [],
    start_time: '',
    end_time: '',
    capacity: '15',
    active: true,
  });

  useEffect(() => {
    if (selectedCenter) {
      fetchBatches();
    }
  }, [selectedCenter, showInactive]);

  const fetchBatches = async () => {
    if (!selectedCenter) return;
    try {
      setLoading(true);
      const params = new URLSearchParams({
        center_id: selectedCenter.id.toString(),
        active_only: (!showInactive).toString(),
      });
      const data = await api.get<Batch[]>(`/api/v1/enrollments/batches?${params}`);
      setBatches(data);
    } catch (error) {
      console.error('Failed to fetch batches:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingBatch(null);
    setFormData({
      name: '',
      age_min: '',
      age_max: '',
      days_of_week: [],
      start_time: '',
      end_time: '',
      capacity: '15',
      active: true,
    });
    setError('');
    setDrawerOpen(true);
  };

  const handleEdit = (batch: Batch) => {
    setEditingBatch(batch);
    setFormData({
      name: batch.name,
      age_min: batch.age_min?.toString() || '',
      age_max: batch.age_max?.toString() || '',
      days_of_week: batch.days_of_week || [],
      start_time: batch.start_time || '',
      end_time: batch.end_time || '',
      capacity: batch.capacity?.toString() || '15',
      active: batch.active,
    });
    setError('');
    setDrawerOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCenter) return;

    setSubmitting(true);
    setError('');

    try {
      const payload: Record<string, unknown> = {
        name: formData.name,
        age_min: formData.age_min ? parseInt(formData.age_min) : null,
        age_max: formData.age_max ? parseInt(formData.age_max) : null,
        days_of_week: formData.days_of_week.length > 0 ? formData.days_of_week : null,
        start_time: formData.start_time || null,
        end_time: formData.end_time || null,
        capacity: formData.capacity ? parseInt(formData.capacity) : null,
        active: formData.active,
      };

      if (editingBatch) {
        await api.patch(`/api/v1/enrollments/batches/${editingBatch.id}`, payload);
      } else {
        await api.post(`/api/v1/enrollments/batches?center_id=${selectedCenter.id}`, payload);
      }

      await fetchBatches();
      setDrawerOpen(false);
    } catch (err: any) {
      setError(err.message || 'Failed to save batch');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (batch: Batch) => {
    if (!confirm(`Are you sure you want to delete/deactivate "${batch.name}"?`)) return;

    try {
      await api.delete(`/api/v1/enrollments/batches/${batch.id}`);
      await fetchBatches();
      setDrawerOpen(false);
    } catch (err: any) {
      setError(err.message || 'Failed to delete batch');
    }
  };

  const toggleDay = (day: string) => {
    setFormData(prev => ({
      ...prev,
      days_of_week: prev.days_of_week.includes(day)
        ? prev.days_of_week.filter(d => d !== day)
        : [...prev.days_of_week, day],
    }));
  };

  if (!selectedCenter) {
    return (
      <div className="p-8 bg-gray-50 min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500 mb-4">Please select a center first</p>
          <button
            onClick={() => router.push('/mdm')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to MDM
          </button>
        </div>
      </div>
    );
  }

  const columns: Column<Batch>[] = [
    {
      key: 'name',
      label: 'Batch Name',
      sortable: true,
      render: (row) => (
        <div className="font-semibold text-gray-900">{row.name}</div>
      ),
    },
    {
      key: 'age_min',
      label: 'Age Range',
      sortable: true,
      sortKey: 'age_min',
      render: (row) => (
        <span className="text-gray-700">
          {row.age_min != null && row.age_max != null
            ? `${row.age_min} - ${row.age_max} years`
            : '-'}
        </span>
      ),
    },
    {
      key: 'days_of_week',
      label: 'Days',
      render: (row) => (
        <div className="flex flex-wrap gap-1">
          {row.days_of_week?.map(day => (
            <span key={day} className="px-1.5 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">
              {day}
            </span>
          )) || <span className="text-gray-400">-</span>}
        </div>
      ),
    },
    {
      key: 'start_time',
      label: 'Time',
      render: (row) => (
        <span className="text-gray-700">
          {row.start_time && row.end_time
            ? `${row.start_time.slice(0, 5)} - ${row.end_time.slice(0, 5)}`
            : '-'}
        </span>
      ),
    },
    {
      key: 'capacity',
      label: 'Capacity',
      sortable: true,
      render: (row) => (
        <span className="text-gray-700">{row.capacity || '-'}</span>
      ),
    },
    {
      key: 'active',
      label: 'Status',
      sortable: true,
      render: (row) =>
        row.active ? (
          <span className="px-2.5 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">
            Active
          </span>
        ) : (
          <span className="px-2.5 py-1 bg-gray-100 text-gray-800 text-xs font-medium rounded">
            Inactive
          </span>
        ),
    },
  ];

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <button
                onClick={() => router.push('/mdm')}
                className="text-gray-500 hover:text-gray-700"
              >
                &larr; Back to MDM
              </button>
            </div>
            <h1 className="text-3xl font-bold text-gray-900">Batches</h1>
            <p className="text-gray-600 mt-1">
              Manage batches for {selectedCenter.name}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-gray-600">
              <input
                type="checkbox"
                checked={showInactive}
                onChange={(e) => setShowInactive(e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded"
              />
              Show inactive
            </label>
            <button
              onClick={handleCreate}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
            >
              + Add Batch
            </button>
          </div>
        </div>

        {/* Table */}
        {batches.length === 0 && !loading ? (
          <EmptyState
            icon={<span className="text-6xl">📅</span>}
            title="No Batches"
            description="Get started by creating your first batch"
            action={{
              label: 'Add Batch',
              onClick: handleCreate,
            }}
          />
        ) : (
          <DataTable
            data={batches}
            columns={columns}
            loading={loading}
            onRowClick={handleEdit}
            emptyMessage="No batches found"
            searchable={true}
            searchPlaceholder="Search batches by name..."
            defaultSortKey="name"
            defaultSortDirection="asc"
          />
        )}

        {/* Drawer */}
        <Drawer
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          title={editingBatch ? 'Edit Batch' : 'Add Batch'}
          size="md"
        >
          <form onSubmit={handleSubmit} className="flex flex-col h-full">
            <div className="flex-1 overflow-y-auto px-6 py-4">
              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
                  {error}
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Batch Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., Funny Bugs, Good Friends"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Min Age (years)
                    </label>
                    <input
                      type="number"
                      value={formData.age_min}
                      onChange={(e) => setFormData({ ...formData, age_min: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      min="0"
                      max="18"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max Age (years)
                    </label>
                    <input
                      type="number"
                      value={formData.age_max}
                      onChange={(e) => setFormData({ ...formData, age_max: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      min="0"
                      max="18"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Days of Week
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {DAYS.map(day => (
                      <button
                        key={day}
                        type="button"
                        onClick={() => toggleDay(day)}
                        className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                          formData.days_of_week.includes(day)
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {day}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Start Time
                    </label>
                    <input
                      type="time"
                      value={formData.start_time}
                      onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      End Time
                    </label>
                    <input
                      type="time"
                      value={formData.end_time}
                      onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Capacity
                  </label>
                  <input
                    type="number"
                    value={formData.capacity}
                    onChange={(e) => setFormData({ ...formData, capacity: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    min="1"
                    max="50"
                  />
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="active"
                    checked={formData.active}
                    onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="active" className="text-sm font-medium text-gray-700">
                    Active
                  </label>
                </div>
              </div>
            </div>

            <div className="border-t border-gray-200 px-6 py-4 flex justify-between">
              <div>
                {editingBatch && (
                  <button
                    type="button"
                    onClick={() => handleDelete(editingBatch)}
                    className="px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-50 transition"
                  >
                    Delete
                  </button>
                )}
              </div>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setDrawerOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
                  disabled={submitting}
                >
                  {submitting ? 'Saving...' : editingBatch ? 'Update' : 'Create'}
                </button>
              </div>
            </div>
          </form>
        </Drawer>
      </div>
    </div>
  );
}
