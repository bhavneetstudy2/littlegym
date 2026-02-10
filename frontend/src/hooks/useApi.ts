// Custom React hooks for API calls

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { useCenter } from '@/contexts/CenterContext';
import type {
  Lead, Enrollment, Batch, ClassSession, Attendance,
  Curriculum, SkillProgress, ReportCard, DashboardStats
} from '@/types';

export function useLeads() {
  const { selectedCenter, isSuperAdmin } = useCenter();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLeads = useCallback(async () => {
    if (isSuperAdmin && !selectedCenter) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const centerParam = selectedCenter ? `?center_id=${selectedCenter.id}` : '';
      const data = await api.get<Lead[]>(`/api/v1/leads${centerParam}`);
      setLeads(data);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch leads';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [selectedCenter, isSuperAdmin]);

  useEffect(() => {
    fetchLeads();
  }, [fetchLeads]);

  return { leads, loading, error, refetch: fetchLeads };
}

export function useEnrollments(status?: string) {
  const { selectedCenter, isSuperAdmin } = useCenter();
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEnrollments = useCallback(async () => {
    if (isSuperAdmin && !selectedCenter) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      let endpoint = '/api/v1/enrollments';
      const params = new URLSearchParams();
      if (selectedCenter) params.append('center_id', selectedCenter.id.toString());
      if (status) params.append('status', status);
      if (params.toString()) endpoint += `?${params.toString()}`;

      const data = await api.get<Enrollment[]>(endpoint);
      setEnrollments(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch enrollments');
    } finally {
      setLoading(false);
    }
  }, [selectedCenter, isSuperAdmin, status]);

  useEffect(() => {
    fetchEnrollments();
  }, [fetchEnrollments]);

  return { enrollments, loading, error, refetch: fetchEnrollments };
}

export function useBatches() {
  const { selectedCenter, isSuperAdmin } = useCenter();
  const [batches, setBatches] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBatches = useCallback(async () => {
    if (isSuperAdmin && !selectedCenter) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const centerParam = selectedCenter ? `?center_id=${selectedCenter.id}` : '';
      const data = await api.get<Batch[]>(`/api/v1/enrollments/batches${centerParam}`);
      setBatches(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch batches');
    } finally {
      setLoading(false);
    }
  }, [selectedCenter, isSuperAdmin]);

  useEffect(() => {
    fetchBatches();
  }, [fetchBatches]);

  return { batches, loading, error, refetch: fetchBatches };
}

export function useClassSessions(date?: string) {
  const { selectedCenter, isSuperAdmin } = useCenter();
  const [sessions, setSessions] = useState<ClassSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = useCallback(async () => {
    if (isSuperAdmin && !selectedCenter) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (selectedCenter) params.append('center_id', selectedCenter.id.toString());
      if (date) params.append('session_date', date);

      const data = await api.get<ClassSession[]>(`/api/v1/attendance/sessions?${params.toString()}`);
      setSessions(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch sessions');
    } finally {
      setLoading(false);
    }
  }, [selectedCenter, isSuperAdmin, date]);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  return { sessions, loading, error, refetch: fetchSessions };
}

export function useCurricula() {
  const [curricula, setCurricula] = useState<Curriculum[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCurricula = async () => {
    try {
      setLoading(true);
      const data = await api.get<Curriculum[]>('/api/v1/curriculum');
      setCurricula(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch curricula');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCurricula();
  }, []);

  return { curricula, loading, error, refetch: fetchCurricula };
}

export function useReportCards(childId?: number) {
  const [reportCards, setReportCards] = useState<ReportCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchReportCards = async () => {
    try {
      setLoading(true);
      const endpoint = childId
        ? `/api/v1/report-cards?child_id=${childId}`
        : '/api/v1/report-cards';
      const data = await api.get<ReportCard[]>(endpoint);
      setReportCards(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch report cards');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReportCards();
  }, [childId]);

  return { reportCards, loading, error, refetch: fetchReportCards };
}

export function useDashboardStats() {
  const { selectedCenter, isSuperAdmin } = useCenter();
  const [stats, setStats] = useState<DashboardStats>({
    total_leads: 0,
    active_enrollments: 0,
    todays_classes: 0,
    pending_renewals: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      if (isSuperAdmin && !selectedCenter) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const centerParam = selectedCenter ? `center_id=${selectedCenter.id}` : '';

        // Fetch data from multiple endpoints
        const [leads, enrollments, sessions] = await Promise.all([
          api.get<Lead[]>(`/api/v1/leads?${centerParam}`),
          api.get<Enrollment[]>(`/api/v1/enrollments?status=ACTIVE&${centerParam}`),
          api.get<ClassSession[]>(`/api/v1/attendance/sessions?session_date=${new Date().toISOString().split('T')[0]}&${centerParam}`),
        ]);

        setStats({
          total_leads: leads.length,
          active_enrollments: enrollments.length,
          todays_classes: sessions.length,
          pending_renewals: 0, // TODO: fix expiring endpoint
        });
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch stats');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [selectedCenter, isSuperAdmin]);

  return { stats, loading, error };
}
