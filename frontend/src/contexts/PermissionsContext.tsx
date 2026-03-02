'use client';

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { api } from '@/lib/api';

interface PermissionsContextType {
  permissions: Record<string, boolean>;
  loading: boolean;
  hasPermission: (key: string) => boolean;
  refetchPermissions: () => Promise<void>;
}

const defaultContext: PermissionsContextType = {
  permissions: {},
  loading: true,
  hasPermission: () => false,
  refetchPermissions: async () => {},
};

const PermissionsContext = createContext<PermissionsContextType>(defaultContext);

export function PermissionsProvider({ children }: { children: ReactNode }) {
  const [permissions, setPermissions] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);

  const fetchPermissions = useCallback(async () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const data = await api.get<{ permissions: Record<string, boolean> }>('/api/v1/settings/my-permissions');
      setPermissions(data.permissions);
    } catch (err) {
      console.error('Failed to fetch permissions:', err);
      // On error, default to empty (no permissions) — admins always get full access server-side
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPermissions();
  }, [fetchPermissions]);

  const hasPermission = useCallback((key: string) => {
    return permissions[key] === true;
  }, [permissions]);

  return (
    <PermissionsContext.Provider value={{ permissions, loading, hasPermission, refetchPermissions: fetchPermissions }}>
      {children}
    </PermissionsContext.Provider>
  );
}

export function usePermissions() {
  return useContext(PermissionsContext);
}
