'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api } from '@/lib/api';
import type { Center } from '@/types/center';

interface CenterContextType {
  selectedCenter: Center | null;
  setSelectedCenter: (center: Center | null) => void;
  centers: Center[];
  loading: boolean;
  isSuperAdmin: boolean;
  refetchCenters: () => Promise<void>;
}

const defaultContext: CenterContextType = {
  selectedCenter: null,
  setSelectedCenter: () => {},
  centers: [],
  loading: false,
  isSuperAdmin: false,
  refetchCenters: async () => {},
};

export const CenterContext = createContext<CenterContextType>(defaultContext);

interface CenterContextProviderProps {
  children: ReactNode;
}

export function CenterContextProvider({ children }: CenterContextProviderProps) {
  const [selectedCenter, setSelectedCenterState] = useState<Center | null>(null);
  const [centers, setCenters] = useState<Center[]>([]);
  const [loading, setLoading] = useState(false);
  const [isSuperAdmin, setIsSuperAdmin] = useState(false);

  // Determine role and fetch centers
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    const initContext = async () => {
      // Read user from localStorage first (stored during login) to avoid extra API call
      const storedUser = localStorage.getItem('user');
      let user: any = null;

      if (storedUser) {
        try {
          user = JSON.parse(storedUser);
        } catch { /* ignore */ }
      }

      // Fallback to API if no stored user
      if (!user) {
        try {
          user = await api.get<any>('/api/v1/auth/me');
        } catch (error) {
          console.error('Failed to fetch user info:', error);
          return;
        }
      }

      const isSuper = user.role === 'SUPER_ADMIN';
      setIsSuperAdmin(isSuper);

      if (isSuper) {
        // Super admin: fetch all centers and restore saved selection
        setLoading(true);
        try {
          const data = await api.get<Center[]>('/api/v1/centers');
          setCenters(data);

          // Restore previously selected center
          const savedCenterId = localStorage.getItem('selectedCenterId');
          if (savedCenterId) {
            const center = data.find(c => c.id === parseInt(savedCenterId));
            if (center) setSelectedCenterState(center);
          }
        } finally {
          setLoading(false);
        }
      } else if (user.center_id) {
        // Center admin: auto-select their center
        await fetchUserCenter(user.center_id);
      }
    };

    initContext();
  }, []);

  const fetchCenters = async () => {
    setLoading(true);
    try {
      const data = await api.get<Center[]>('/api/v1/centers');
      setCenters(data);
    } catch (error) {
      console.error('Failed to fetch centers:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserCenter = async (centerId: number) => {
    setLoading(true);
    try {
      const data = await api.get<Center>(`/api/v1/centers/${centerId}`);
      setSelectedCenterState(data);
      setCenters([data]);
    } catch (error) {
      console.error('Failed to fetch user center:', error);
    } finally {
      setLoading(false);
    }
  };

  const setSelectedCenter = (center: Center | null) => {
    setSelectedCenterState(center);

    // Persist to localStorage for super admin
    if (isSuperAdmin) {
      if (center) {
        localStorage.setItem('selectedCenterId', center.id.toString());
      } else {
        localStorage.removeItem('selectedCenterId');
      }
    }
  };

  const refetchCenters = async () => {
    if (isSuperAdmin) {
      await fetchCenters();
    }
  };

  return (
    <CenterContext.Provider
      value={{
        selectedCenter,
        setSelectedCenter,
        centers,
        loading,
        isSuperAdmin,
        refetchCenters,
      }}
    >
      {children}
    </CenterContext.Provider>
  );
}

// Hook to use the center context
export function useCenter() {
  const context = useContext(CenterContext);
  if (!context) {
    throw new Error('useCenter must be used within a CenterContextProvider');
  }
  return context;
}
