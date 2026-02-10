// Center-related type definitions

export interface Center {
  id: number;
  name: string;
  code: string | null;
  city: string | null;
  state: string | null;
  timezone: string;
  address: string | null;
  phone: string | null;
  email: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CenterStats {
  center_id: number;
  center_name: string;
  total_leads: number;
  active_enrollments: number;
  total_batches: number;
  total_users: number;
  last_activity: string | null;
}
