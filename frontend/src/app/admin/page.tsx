'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { useCenter } from '@/contexts/CenterContext';
import type { User } from '@/types';

interface Center {
  id: number;
  name: string;
  city: string;
  address: string;
  phone: string;
  timezone: string;
  created_at: string;
}

interface PermissionDefinition {
  key: string;
  label: string;
  category: 'module' | 'action';
}

interface RolePermissions {
  role: string;
  permissions: Record<string, boolean>;
}

interface PermissionsConfig {
  definitions: PermissionDefinition[];
  roles: RolePermissions[];
}

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<'users' | 'permissions' | 'centers'>('users');
  const [users, setUsers] = useState<User[]>([]);
  const [centers, setCenters] = useState<Center[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUserModal, setShowUserModal] = useState(false);
  const [showCenterModal, setShowCenterModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  useEffect(() => {
    fetchCurrentUser();
  }, []);

  useEffect(() => {
    if (currentUser) {
      if (activeTab === 'users') {
        fetchUsers();
      } else if (activeTab === 'centers') {
        fetchCenters();
      }
    }
  }, [activeTab, currentUser]);

  const fetchCurrentUser = async () => {
    try {
      const user = await api.get<User>('/api/v1/auth/me');
      setCurrentUser(user);
    } catch (err) {
      console.error('Failed to fetch current user:', err);
    }
  };

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const data = await api.get<User[]>('/api/v1/users');
      setUsers(data);
    } catch (err) {
      console.error('Failed to fetch users:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchCenters = async () => {
    try {
      setLoading(true);
      const data = await api.get<Center[]>('/api/v1/centers');
      setCenters(data);
    } catch (err) {
      console.error('Failed to fetch centers:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeactivate = async (user: User) => {
    const newStatus = user.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';
    const label = newStatus === 'INACTIVE' ? 'deactivate' : 'reactivate';
    if (!confirm(`Are you sure you want to ${label} ${user.name}?`)) return;
    try {
      await api.patch(`/api/v1/users/${user.id}/status`, { status: newStatus });
      fetchUsers();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update user status');
    }
  };

  const isSuperAdmin = currentUser?.role === 'SUPER_ADMIN';

  if (!currentUser) {
    return (
      <div className="p-6">
        <div className="text-center text-gray-500">Loading...</div>
      </div>
    );
  }

  if (!isSuperAdmin && currentUser.role !== 'CENTER_ADMIN') {
    return (
      <div className="p-6">
        <div className="text-center text-red-500">
          Access denied. This page is only available to administrators.
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Administration</h1>
          <p className="text-gray-600">Manage users, permissions, and centers</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('users')}
            className={`flex-1 px-6 py-4 text-center font-medium transition ${
              activeTab === 'users'
                ? 'border-b-2 border-blue-500 text-blue-600 bg-blue-50'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            Users
          </button>
          <button
            onClick={() => setActiveTab('permissions')}
            className={`flex-1 px-6 py-4 text-center font-medium transition ${
              activeTab === 'permissions'
                ? 'border-b-2 border-blue-500 text-blue-600 bg-blue-50'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            Permissions
          </button>
          {isSuperAdmin && (
            <button
              onClick={() => setActiveTab('centers')}
              className={`flex-1 px-6 py-4 text-center font-medium transition ${
                activeTab === 'centers'
                  ? 'border-b-2 border-blue-500 text-blue-600 bg-blue-50'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              Centers
            </button>
          )}
        </div>
      </div>

      {/* Users Tab */}
      {activeTab === 'users' && (
        <div>
          <div className="mb-4 flex justify-end">
            <button
              onClick={() => setShowUserModal(true)}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
            >
              + Add User
            </button>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            {loading ? (
              <div className="p-8 text-center text-gray-500">Loading users...</div>
            ) : users.length === 0 ? (
              <div className="p-8 text-center text-gray-500">No users found</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Email
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Role
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {users.map((user) => (
                      <tr key={user.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{user.name}</div>
                          {user.phone && (
                            <div className="text-xs text-gray-400">{user.phone}</div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {user.email}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                            {user.role}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`px-2 py-1 text-xs font-semibold rounded-full ${
                              user.status === 'ACTIVE'
                                ? 'bg-green-100 text-green-800'
                                : 'bg-red-100 text-red-800'
                            }`}
                          >
                            {user.status === 'ACTIVE' ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => setEditingUser(user)}
                            className="text-blue-600 hover:text-blue-900 mr-3"
                          >
                            Edit
                          </button>
                          {user.id !== currentUser.id && (
                            <button
                              onClick={() => handleDeactivate(user)}
                              className={user.status === 'ACTIVE' ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'}
                            >
                              {user.status === 'ACTIVE' ? 'Deactivate' : 'Reactivate'}
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Permissions Tab */}
      {activeTab === 'permissions' && (
        <PermissionsTab isSuperAdmin={isSuperAdmin} currentUser={currentUser} />
      )}

      {/* Centers Tab */}
      {activeTab === 'centers' && isSuperAdmin && (
        <div>
          <div className="mb-4 flex justify-end">
            <button
              onClick={() => setShowCenterModal(true)}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
            >
              + Add Center
            </button>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            {loading ? (
              <div className="p-8 text-center text-gray-500">Loading centers...</div>
            ) : centers.length === 0 ? (
              <div className="p-8 text-center text-gray-500">No centers found</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        City
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Phone
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Created
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {centers.map((center) => (
                      <tr key={center.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{center.name}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {center.city}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {center.phone}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(center.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button className="text-blue-600 hover:text-blue-900 mr-3">
                            Edit
                          </button>
                          <button className="text-green-600 hover:text-green-900">
                            View Details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Add User Modal */}
      {showUserModal && (
        <AddUserModal
          onClose={() => setShowUserModal(false)}
          onSuccess={() => {
            setShowUserModal(false);
            fetchUsers();
          }}
          isSuperAdmin={isSuperAdmin}
          currentCenterId={currentUser.center_id}
        />
      )}

      {/* Edit User Modal */}
      {editingUser && (
        <EditUserModal
          user={editingUser}
          onClose={() => setEditingUser(null)}
          onSuccess={() => {
            setEditingUser(null);
            fetchUsers();
          }}
          isSuperAdmin={isSuperAdmin}
          currentUserId={currentUser.id}
        />
      )}

      {/* Add Center Modal */}
      {showCenterModal && (
        <AddCenterModal
          onClose={() => setShowCenterModal(false)}
          onSuccess={() => {
            setShowCenterModal(false);
            fetchCenters();
          }}
        />
      )}
    </div>
  );
}

// ─── Permissions Tab ─────────────────────────────────────────────────────────

const ROLE_LABELS: Record<string, string> = {
  CENTER_MANAGER: 'Center Manager',
  TRAINER: 'Trainer',
  COUNSELOR: 'Counselor',
};

function PermissionsTab({ isSuperAdmin, currentUser }: { isSuperAdmin: boolean; currentUser: User }) {
  const { selectedCenter } = useCenter();
  const [config, setConfig] = useState<PermissionsConfig | null>(null);
  const [editedPerms, setEditedPerms] = useState<Record<string, Record<string, boolean>>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  const [hasChanges, setHasChanges] = useState(false);

  const centerId = isSuperAdmin ? selectedCenter?.id : currentUser.center_id;

  useEffect(() => {
    if (centerId) {
      fetchPermissions();
    }
  }, [centerId]);

  const fetchPermissions = async () => {
    if (!centerId) return;
    try {
      setLoading(true);
      const params = isSuperAdmin ? `?center_id=${centerId}` : '';
      const data = await api.get<PermissionsConfig>(`/api/v1/settings/permissions${params}`);
      setConfig(data);

      const perms: Record<string, Record<string, boolean>> = {};
      for (const role of data.roles) {
        perms[role.role] = { ...role.permissions };
      }
      setEditedPerms(perms);
      setHasChanges(false);
    } catch (err) {
      console.error('Failed to fetch permissions:', err);
    } finally {
      setLoading(false);
    }
  };

  const togglePermission = (role: string, key: string) => {
    setEditedPerms(prev => ({
      ...prev,
      [role]: {
        ...prev[role],
        [key]: !prev[role][key],
      },
    }));
    setHasChanges(true);
    setSaveMessage('');
  };

  const saveAllPermissions = async () => {
    if (!centerId) return;
    setSaving(true);
    setSaveMessage('');
    try {
      for (const role of Object.keys(editedPerms)) {
        await api.put('/api/v1/settings/permissions', {
          center_id: centerId,
          role,
          permissions: editedPerms[role],
        });
      }
      setSaveMessage('All permissions saved successfully!');
      setHasChanges(false);
      setTimeout(() => setSaveMessage(''), 3000);
    } catch (err) {
      setSaveMessage(`Failed to save: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setSaving(false);
    }
  };

  if (!centerId) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
        {isSuperAdmin
          ? 'Please select a center from the top bar to configure permissions.'
          : 'No center assigned to your account.'}
      </div>
    );
  }

  if (loading) {
    return <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">Loading permissions...</div>;
  }

  if (!config) {
    return <div className="bg-white rounded-lg shadow p-8 text-center text-red-500">Failed to load permissions.</div>;
  }

  const modulePerms = config.definitions.filter(d => d.category === 'module');
  const actionPerms = config.definitions.filter(d => d.category === 'action');
  const roles = config.roles.map(r => r.role);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-gray-500">
          Configure which modules and actions each role can access. Super Admin and Center Admin always have full access.
        </p>
        <button
          onClick={saveAllPermissions}
          disabled={saving || !hasChanges}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save All Changes'}
        </button>
      </div>

      {saveMessage && (
        <div className={`mb-4 p-3 rounded-lg text-sm font-medium ${
          saveMessage.includes('Failed') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
        }`}>
          {saveMessage}
        </div>
      )}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider w-64">
                  Permission
                </th>
                {roles.map(role => (
                  <th key={role} className="px-6 py-4 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    {ROLE_LABELS[role] || role}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr>
                <td colSpan={roles.length + 1} className="px-6 py-3 bg-blue-50 border-b border-blue-100">
                  <span className="text-sm font-bold text-blue-700">Module Access</span>
                  <span className="text-xs text-blue-500 ml-2">Which pages the role can see in the sidebar</span>
                </td>
              </tr>
              {modulePerms.map(perm => (
                <tr key={perm.key} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-6 py-3">
                    <span className="text-sm font-medium text-gray-700">{perm.label}</span>
                  </td>
                  {roles.map(role => (
                    <td key={role} className="px-6 py-3 text-center">
                      <button
                        onClick={() => togglePermission(role, perm.key)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 ${
                          editedPerms[role]?.[perm.key] ? 'bg-blue-600' : 'bg-gray-300'
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow ${
                            editedPerms[role]?.[perm.key] ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </td>
                  ))}
                </tr>
              ))}

              <tr>
                <td colSpan={roles.length + 1} className="px-6 py-3 bg-purple-50 border-b border-purple-100">
                  <span className="text-sm font-bold text-purple-700">Action Permissions</span>
                  <span className="text-xs text-purple-500 ml-2">Specific capabilities within the app</span>
                </td>
              </tr>
              {actionPerms.map(perm => (
                <tr key={perm.key} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-6 py-3">
                    <span className="text-sm font-medium text-gray-700">{perm.label}</span>
                  </td>
                  {roles.map(role => (
                    <td key={role} className="px-6 py-3 text-center">
                      <button
                        onClick={() => togglePermission(role, perm.key)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 ${
                          editedPerms[role]?.[perm.key] ? 'bg-blue-600' : 'bg-gray-300'
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow ${
                            editedPerms[role]?.[perm.key] ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ─── Add User Modal ──────────────────────────────────────────────────────────

function AddUserModal({
  onClose,
  onSuccess,
  isSuperAdmin,
  currentCenterId,
}: {
  onClose: () => void;
  onSuccess: () => void;
  isSuperAdmin: boolean;
  currentCenterId: number | null | undefined;
}) {
  const [centers, setCenters] = useState<Center[]>([]);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    phone: '',
    role: 'TRAINER',
    center_id: currentCenterId ? String(currentCenterId) : '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isSuperAdmin) {
      api.get<Center[]>('/api/v1/centers').then(setCenters).catch(console.error);
    }
  }, [isSuperAdmin]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      await api.post('/api/v1/users', {
        name: formData.name,
        email: formData.email,
        password: formData.password,
        phone: formData.phone || undefined,
        role: formData.role,
        center_id: formData.role === 'SUPER_ADMIN' ? null : Number(formData.center_id),
      });
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create user');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-md w-full p-6">
        <h2 className="text-2xl font-bold mb-4">Add New User</h2>
        {error && <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password *</label>
            <input
              type="password"
              required
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
            <input
              type="tel"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Role *</label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              {isSuperAdmin && <option value="SUPER_ADMIN">Super Admin</option>}
              {isSuperAdmin && <option value="CENTER_ADMIN">Center Admin</option>}
              <option value="CENTER_MANAGER">Center Manager</option>
              <option value="TRAINER">Trainer</option>
              <option value="COUNSELOR">Counselor</option>
            </select>
          </div>

          {formData.role !== 'SUPER_ADMIN' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Center *</label>
              {isSuperAdmin ? (
                <select
                  required
                  value={formData.center_id}
                  onChange={(e) => setFormData({ ...formData, center_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">-- Select center --</option>
                  {centers.map((center) => (
                    <option key={center.id} value={center.id}>
                      {center.name}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  disabled
                  value="Your Center (auto-assigned)"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-500"
                />
              )}
            </div>
          )}

          <div className="flex gap-3 mt-6">
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium disabled:opacity-50"
            >
              {submitting ? 'Creating...' : 'Create User'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition font-medium"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Edit User Modal ─────────────────────────────────────────────────────────

function EditUserModal({
  user,
  onClose,
  onSuccess,
  isSuperAdmin,
  currentUserId,
}: {
  user: User;
  onClose: () => void;
  onSuccess: () => void;
  isSuperAdmin: boolean;
  currentUserId: number;
}) {
  const [formData, setFormData] = useState({
    name: user.name,
    email: user.email,
    phone: user.phone || '',
    role: user.role,
    password: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      const payload: Record<string, string> = {
        name: formData.name,
        email: formData.email,
        phone: formData.phone,
        role: formData.role,
      };
      if (formData.password) {
        payload.password = formData.password;
      }
      await api.patch(`/api/v1/users/${user.id}`, payload);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update user');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-md w-full p-6">
        <h2 className="text-2xl font-bold mb-4">Edit User</h2>
        {error && <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
            <input
              type="tel"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Role *</label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value as User['role'] })}
              disabled={user.id === currentUserId}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
            >
              {isSuperAdmin && <option value="SUPER_ADMIN">Super Admin</option>}
              {isSuperAdmin && <option value="CENTER_ADMIN">Center Admin</option>}
              <option value="CENTER_MANAGER">Center Manager</option>
              <option value="TRAINER">Trainer</option>
              <option value="COUNSELOR">Counselor</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              New Password <span className="text-gray-400 font-normal">(leave blank to keep current)</span>
            </label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              placeholder="Enter new password..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex gap-3 mt-6">
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium disabled:opacity-50"
            >
              {submitting ? 'Saving...' : 'Save Changes'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition font-medium"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Add Center Modal ────────────────────────────────────────────────────────

function AddCenterModal({
  onClose,
  onSuccess,
}: {
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState({
    name: '',
    city: '',
    address: '',
    phone: '',
    timezone: 'Asia/Kolkata',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      await api.post('/api/v1/centers', formData);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create center');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-md w-full p-6">
        <h2 className="text-2xl font-bold mb-4">Add New Center</h2>
        {error && <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">City *</label>
            <input
              type="text"
              required
              value={formData.city}
              onChange={(e) => setFormData({ ...formData, city: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Address *</label>
            <textarea
              required
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Phone *</label>
            <input
              type="tel"
              required
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Timezone</label>
            <input
              type="text"
              value={formData.timezone}
              onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex gap-3 mt-6">
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium disabled:opacity-50"
            >
              {submitting ? 'Creating...' : 'Create Center'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition font-medium"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
