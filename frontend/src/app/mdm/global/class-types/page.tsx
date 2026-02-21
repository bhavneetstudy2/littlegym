'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import DataTable, { Column } from '@/components/ui/DataTable';
import Drawer from '@/components/ui/Drawer';
import EmptyState from '@/components/ui/EmptyState';

interface ClassType {
  id: number;
  name: string;
  description: string;
  age_min: number;
  age_max: number;
  duration_minutes: number;
  active: boolean;
}

interface ClassTypeFormData {
  name: string;
  description: string;
  age_min: string;
  age_max: string;
  duration_minutes: string;
  active: boolean;
}

export default function ClassTypesPage() {
  const router = useRouter();
  const [classTypes, setClassTypes] = useState<ClassType[]>([]);
  const [loading, setLoading] = useState(true);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingClassType, setEditingClassType] = useState<ClassType | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState<ClassTypeFormData>({
    name: '',
    description: '',
    age_min: '',
    age_max: '',
    duration_minutes: '45',
    active: true,
  });

  useEffect(() => {
    fetchClassTypes();
  }, []);

  const fetchClassTypes = async () => {
    try {
      setLoading(true);
      const data = await api.get<ClassType[]>('/api/v1/mdm/class-types');
      setClassTypes(data);
    } catch (error) {
      console.error('Failed to fetch class types:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingClassType(null);
    setFormData({
      name: '',
      description: '',
      age_min: '',
      age_max: '',
      duration_minutes: '45',
      active: true,
    });
    setError('');
    setDrawerOpen(true);
  };

  const handleEdit = (classType: ClassType) => {
    setEditingClassType(classType);
    setFormData({
      name: classType.name,
      description: classType.description || '',
      age_min: classType.age_min.toString(),
      age_max: classType.age_max.toString(),
      duration_minutes: classType.duration_minutes.toString(),
      active: classType.active,
    });
    setError('');
    setDrawerOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      const payload = {
        name: formData.name,
        description: formData.description || null,
        age_min: parseInt(formData.age_min),
        age_max: parseInt(formData.age_max),
        duration_minutes: parseInt(formData.duration_minutes),
        active: formData.active,
      };

      if (editingClassType) {
        await api.patch(`/api/v1/mdm/class-types/${editingClassType.id}`, payload);
      } else {
        await api.post('/api/v1/mdm/class-types', payload);
      }

      await fetchClassTypes();
      setDrawerOpen(false);
    } catch (err: any) {
      setError(err.message || 'Failed to save class type');
    } finally {
      setSubmitting(false);
    }
  };

  const columns: Column<ClassType>[] = [
    {
      key: 'name',
      label: 'Class Type',
      sortable: true,
      render: (row) => (
        <div>
          <div className="font-semibold text-gray-900">{row.name}</div>
          {row.description && <div className="text-sm text-gray-500">{row.description}</div>}
        </div>
      ),
    },
    {
      key: 'age_min',
      label: 'Age Range',
      sortable: true,
      sortKey: 'age_min',
      render: (row) => (
        <span className="text-gray-700">
          {row.age_min} - {row.age_max} years
        </span>
      ),
    },
    {
      key: 'duration_minutes',
      label: 'Duration',
      sortable: true,
      render: (row) => <span className="text-gray-700">{row.duration_minutes} mins</span>,
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
                ← Back to MDM
              </button>
            </div>
            <h1 className="text-3xl font-bold text-gray-900">Class Types</h1>
            <p className="text-gray-600 mt-1">
              Manage global class type definitions used across all centers
            </p>
          </div>
          <button
            onClick={handleCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
          >
            + Add Class Type
          </button>
        </div>

        {/* Table */}
        {classTypes.length === 0 && !loading ? (
          <EmptyState
            icon={<span className="text-6xl">🎯</span>}
            title="No Class Types"
            description="Get started by creating your first class type"
            action={{
              label: 'Add Class Type',
              onClick: handleCreate,
            }}
          />
        ) : (
          <DataTable
            data={classTypes}
            columns={columns}
            loading={loading}
            onRowClick={handleEdit}
            emptyMessage="No class types found"
            searchable={true}
            searchPlaceholder="Search class types by name..."
            defaultSortKey="name"
            defaultSortDirection="asc"
          />
        )}

        {/* Drawer */}
        <Drawer
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          title={editingClassType ? 'Edit Class Type' : 'Add Class Type'}
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
                    Class Type Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., Birds, Bugs, Beasts"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows={3}
                    placeholder="Brief description of this class type"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Min Age (years) *
                    </label>
                    <input
                      type="number"
                      value={formData.age_min}
                      onChange={(e) => setFormData({ ...formData, age_min: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      min="0"
                      max="18"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max Age (years) *
                    </label>
                    <input
                      type="number"
                      value={formData.age_max}
                      onChange={(e) => setFormData({ ...formData, age_max: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      min="0"
                      max="18"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Duration (minutes) *
                  </label>
                  <input
                    type="number"
                    value={formData.duration_minutes}
                    onChange={(e) =>
                      setFormData({ ...formData, duration_minutes: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    min="15"
                    max="180"
                    step="15"
                    required
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

            <div className="border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
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
                {submitting ? 'Saving...' : editingClassType ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </Drawer>
      </div>
    </div>
  );
}
