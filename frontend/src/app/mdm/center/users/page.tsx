'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { useCenter } from '@/contexts/CenterContext';

interface CenterUser {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  role: string;
  status: string;
  center_id: number | null;
}

interface Center {
  id: number;
  name: string;
}

const ROLE_LABELS: Record<string, string> = {
  SUPER_ADMIN: 'Super Admin',
  CENTER_ADMIN: 'Center Admin',
  CENTER_MANAGER: 'Center Manager',
  TRAINER: 'Trainer',
  COUNSELOR: 'Counselor',
};

const ROLE_COLORS: Record<string, string> = {
  SUPER_ADMIN: 'bg-purple-100 text-purple-800',
  CENTER_ADMIN: 'bg-blue-100 text-blue-800',
  CENTER_MANAGER: 'bg-indigo-100 text-indigo-800',
  TRAINER: 'bg-green-100 text-green-800',
  COUNSELOR: 'bg-orange-100 text-orange-800',
};

export default function MDMUsersPage() {
  const router = useRouter();
  const { user: currentUser } = useAuth();
  const { selectedCenter } = useCenter();

  const [users, setUsers] = useState<CenterUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingUser, setEditingUser] = useState<CenterUser | null>(null);
  const [error, setError] = useState('');

  const isSuperAdmin = currentUser?.role === 'SUPER_ADMIN';
  const effectiveCenterId = isSuperAdmin ? selectedCenter?.id : currentUser?.center_id;

  const fetchUsers = async () => {
    if (!effectiveCenterId) return;
    setLoading(true);
    try {
      const params = isSuperAdmin ? `?center_id=${effectiveCenterId}` : '';
      const data = await api.get<CenterUser[]>(`/api/v1/users${params}`);
      setUsers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [effectiveCenterId]);

  const handleToggleStatus = async (user: CenterUser) => {
    const newStatus = user.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';
    if (!confirm(`${newStatus === 'INACTIVE' ? 'Deactivate' : 'Reactivate'} ${user.name}?`)) return;
    try {
      await api.patch(`/api/v1/users/${user.id}/status`, { status: newStatus });
      fetchUsers();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update status');
    }
  };

  if (!effectiveCenterId) {
    return (
      <div className="p-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6 text-yellow-800 text-sm">
          Please select a center to manage users.
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => router.push('/mdm')} className="text-gray-400 hover:text-gray-600 text-sm">
          ← Master Data
        </button>
        <span className="text-gray-300">/</span>
        <h1 className="text-xl font-bold text-gray-900">Users</h1>
        {selectedCenter && (
          <span className="px-2.5 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
            {selectedCenter.name}
          </span>
        )}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <p className="text-sm text-gray-500">{users.length} user{users.length !== 1 ? 's' : ''}</p>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition"
          >
            + Add User
          </button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-400 text-sm">Loading users...</div>
        ) : users.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-sm">No users found for this center.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-100">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Name</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Email</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Role</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {users.map(u => (
                  <tr key={u.id} className="hover:bg-gray-50 transition">
                    <td className="px-5 py-3">
                      <div className="text-sm font-medium text-gray-900">{u.name}</div>
                      {u.phone && <div className="text-xs text-gray-400 mt-0.5">{u.phone}</div>}
                    </td>
                    <td className="px-5 py-3 text-sm text-gray-600">{u.email}</td>
                    <td className="px-5 py-3">
                      <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${ROLE_COLORS[u.role] ?? 'bg-gray-100 text-gray-700'}`}>
                        {ROLE_LABELS[u.role] ?? u.role}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${u.status === 'ACTIVE' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {u.status === 'ACTIVE' ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setEditingUser(u)}
                          className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                        >
                          Edit
                        </button>
                        {u.id !== currentUser?.id && (
                          <button
                            onClick={() => handleToggleStatus(u)}
                            className={`text-xs font-medium ${u.status === 'ACTIVE' ? 'text-red-500 hover:text-red-700' : 'text-green-600 hover:text-green-800'}`}
                          >
                            {u.status === 'ACTIVE' ? 'Deactivate' : 'Reactivate'}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showAddModal && (
        <UserFormModal
          mode="add"
          isSuperAdmin={isSuperAdmin}
          centerId={effectiveCenterId}
          onClose={() => setShowAddModal(false)}
          onSuccess={() => { setShowAddModal(false); fetchUsers(); }}
        />
      )}

      {editingUser && (
        <UserFormModal
          mode="edit"
          user={editingUser}
          isSuperAdmin={isSuperAdmin}
          centerId={effectiveCenterId}
          onClose={() => setEditingUser(null)}
          onSuccess={() => { setEditingUser(null); fetchUsers(); }}
        />
      )}
    </div>
  );
}

// ── User Form Modal ───────────────────────────────────────────────────────────

function UserFormModal({
  mode,
  user,
  isSuperAdmin,
  centerId,
  onClose,
  onSuccess,
}: {
  mode: 'add' | 'edit';
  user?: CenterUser;
  isSuperAdmin: boolean;
  centerId: number;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [form, setForm] = useState({
    name: user?.name ?? '',
    email: user?.email ?? '',
    phone: user?.phone ?? '',
    role: user?.role ?? 'TRAINER',
    password: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      if (mode === 'add') {
        await api.post('/api/v1/users', {
          name: form.name,
          email: form.email,
          phone: form.phone || undefined,
          role: form.role,
          password: form.password,
          center_id: form.role === 'SUPER_ADMIN' ? null : centerId,
        });
      } else {
        const payload: Record<string, string> = { name: form.name, email: form.email, role: form.role };
        if (form.phone) payload.phone = form.phone;
        if (form.password) payload.password = form.password;
        await api.patch(`/api/v1/users/${user!.id}`, payload);
      }
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save user');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl w-full max-w-md shadow-xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 className="font-bold text-gray-900">{mode === 'add' ? 'Add User' : 'Edit User'}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
        </div>
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {error && <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>}

          <div>
            <label className="block text-xs font-semibold text-gray-500 mb-1">Name *</label>
            <input required value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 mb-1">Email *</label>
            <input required type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 mb-1">Phone</label>
            <input type="tel" value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))}
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 mb-1">Role *</label>
            <select value={form.role} onChange={e => setForm(f => ({ ...f, role: e.target.value }))}
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white">
              {isSuperAdmin && <option value="CENTER_ADMIN">Center Admin</option>}
              <option value="CENTER_MANAGER">Center Manager</option>
              <option value="TRAINER">Trainer</option>
              <option value="COUNSELOR">Counselor</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 mb-1">
              {mode === 'add' ? 'Password *' : 'New Password'}
              {mode === 'edit' && <span className="text-gray-400 font-normal ml-1">(leave blank to keep current)</span>}
            </label>
            <input type="password" required={mode === 'add'} value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              placeholder={mode === 'edit' ? 'Enter to change...' : ''}
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>

          <div className="flex gap-3 pt-2">
            <button type="submit" disabled={submitting}
              className="flex-1 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition">
              {submitting ? 'Saving...' : mode === 'add' ? 'Create User' : 'Save Changes'}
            </button>
            <button type="button" onClick={onClose}
              className="flex-1 py-2.5 border border-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
