// Type definitions for all backend models and API responses

export interface User {
  id: number;
  name: string;
  email: string;
  phone: string;
  role: 'SUPER_ADMIN' | 'CENTER_ADMIN' | 'CENTER_MANAGER' | 'TRAINER' | 'COUNSELOR';
  status: 'ACTIVE' | 'INACTIVE';
  center_id: number | null;
}

export interface Child {
  id: number;
  center_id: number;
  first_name: string;
  last_name: string | null;
  dob: string | null;
  school: string | null;
  interests: string[] | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Parent {
  id: number;
  center_id: number;
  name: string;
  phone: string;
  email: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Lead {
  id: number;
  center_id: number;
  child_id: number;
  status: 'DISCOVERY' | 'INTRO_SCHEDULED' | 'INTRO_ATTENDED' | 'NO_SHOW' | 'FOLLOW_UP' | 'DEAD_LEAD' | 'ENROLLED';
  source: 'WALK_IN' | 'REFERRAL' | 'INSTAGRAM' | 'FACEBOOK' | 'GOOGLE' | 'OTHER' | null;
  discovery_notes: string | null;
  dead_lead_reason: string | null;
  assigned_to_user_id: number | null;
  created_at: string;
  updated_at: string;
  child: Child;
}

export interface IntroVisit {
  id: number;
  center_id: number;
  lead_id: number;
  batch_id: number | null;
  scheduled_at: string;
  attended_at: string | null;
  trainer_user_id: number | null;
  outcome_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Batch {
  id: number;
  center_id: number;
  name: string;
  age_min: number | null;
  age_max: number | null;
  days_of_week: string[] | null;
  start_time: string | null;
  end_time: string | null;
  capacity: number | null;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Enrollment {
  id: number;
  center_id: number;
  child_id: number;
  batch_id: number | null;
  plan_type: 'PAY_PER_VISIT' | 'WEEKLY' | 'MONTHLY' | 'QUARTERLY' | 'YEARLY' | 'CUSTOM';
  start_date: string | null;
  end_date: string | null;
  visits_included: number | null;
  visits_used: number;
  days_selected: string[] | null;
  status: 'ACTIVE' | 'EXPIRED' | 'CANCELLED' | 'PAUSED';
  notes: string | null;
  created_at: string;
  updated_at: string;
  // Optional relations returned by backend
  child?: Child;
  batch?: Batch;
}

export interface Payment {
  id: number;
  center_id: number;
  enrollment_id: number;
  amount: string;
  currency: string;
  method: 'CASH' | 'UPI' | 'CARD' | 'BANK_TRANSFER' | 'OTHER';
  reference: string | null;
  paid_at: string;
  discount_total: string | null;
  net_amount: string;
  created_at: string;
}

export interface Discount {
  id: number;
  center_id: number;
  enrollment_id: number;
  type: 'PERCENT' | 'FLAT';
  value: string;
  reason: string | null;
  approved_by_user_id: number | null;
  applied_at: string;
  created_at: string;
}

export interface ClassSession {
  id: number;
  center_id: number;
  batch_id: number;
  session_date: string;
  start_time: string | null;
  end_time: string | null;
  trainer_user_id: number | null;
  status: 'SCHEDULED' | 'COMPLETED' | 'CANCELLED';
  created_at: string;
  updated_at: string;
}

export interface Attendance {
  id: number;
  center_id: number;
  class_session_id: number;
  child_id: number;
  enrollment_id: number | null;
  status: 'PRESENT' | 'ABSENT' | 'MAKEUP' | 'TRIAL' | 'CANCELLED';
  marked_by_user_id: number | null;
  marked_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Curriculum {
  id: number;
  name: string;
  description: string | null;
  center_id: number | null;
  is_global: boolean;
  active: boolean;
  curriculum_type: 'GYMNASTICS' | 'GRADE_SCHOOL';
  created_at: string;
  updated_at: string;
}

export interface Skill {
  id: number;
  curriculum_id: number;
  name: string;
  category: string | null;
  description: string | null;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface SkillProgress {
  id: number;
  center_id: number;
  child_id: number;
  skill_id: number;
  level: 'NOT_STARTED' | 'IN_PROGRESS' | 'ACHIEVED' | 'MASTERED';
  last_updated_at: string | null;
  updated_by_user_id: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  skill?: Skill;
}

export interface ReportCard {
  id: number;
  center_id: number;
  child_id: number;
  period_start: string;
  period_end: string;
  generated_at: string;
  generated_by_user_id: number | null;
  summary_notes: string | null;
  skill_snapshot: any;
  created_at: string;
  updated_at: string;
  // Optional relations
  child?: Child;
}

// ── Weekly Progress Tracking ──

export type MeasurementType = 'LEVEL' | 'COUNT' | 'TIME' | 'MEASUREMENT';

export interface ProgressionLevel {
  id: number;
  activity_category_id: number;
  level_number: number;
  name: string;
  description: string | null;
}

export interface ActivityCategory {
  id: number;
  curriculum_id: number;
  name: string;
  category_group: string | null;
  measurement_type: MeasurementType;
  measurement_unit: string | null;
  display_order: number;
  description: string | null;
  progression_levels: ProgressionLevel[];
  created_at: string;
  updated_at: string;
}

export interface WeeklyProgressEntry {
  activity_category_id: number;
  progression_level_id: number | null;
  numeric_value: number | null;
  notes: string | null;
}

export interface WeeklyProgressBulkPayload {
  child_id: number;
  enrollment_id: number | null;
  week_number: number;
  week_start_date: string;
  entries: WeeklyProgressEntry[];
}

export interface WeeklyProgressResponse {
  id: number;
  center_id: number;
  child_id: number;
  enrollment_id: number | null;
  activity_category_id: number;
  week_number: number;
  week_start_date: string;
  progression_level_id: number | null;
  numeric_value: number | null;
  notes: string | null;
  updated_by_user_id: number | null;
  last_updated_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface WeeklyProgressWeekSummary {
  week_number: number;
  week_start_date: string;
  total_activities: number;
  completed_activities: number;
}

export interface ChildTrainerNotes {
  id: number;
  center_id: number;
  child_id: number;
  enrollment_id: number | null;
  parent_expectation: string | null;
  progress_check: string | null;
  updated_by_user_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface BatchStudentProgressSummary {
  child_id: number;
  child_name: string;
  enrollment_id: number | null;
  enrollment_start_date: string | null;
  current_week: number;
  latest_recorded_week: number | null;
  total_activities: number;
  completed_activities: number;
}

// Dashboard stats interface
export interface DashboardStats {
  total_leads: number;
  active_enrollments: number;
  todays_classes: number;
  pending_renewals: number;
}
