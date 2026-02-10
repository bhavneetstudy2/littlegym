// Enhanced Leads Lifecycle Types

export type LeadStatus =
  | 'ENQUIRY_RECEIVED'
  | 'DISCOVERY_COMPLETED'
  | 'IV_SCHEDULED'
  | 'IV_COMPLETED'
  | 'IV_NO_SHOW'
  | 'FOLLOW_UP_PENDING'
  | 'CONVERTED'
  | 'CLOSED_LOST';

export type LeadSource =
  | 'WALK_IN'
  | 'PHONE_CALL'
  | 'ONLINE'
  | 'REFERRAL'
  | 'INSTAGRAM'
  | 'FACEBOOK'
  | 'GOOGLE'
  | 'OTHER';

export type IVOutcome =
  | 'INTERESTED_ENROLL_NOW'
  | 'INTERESTED_ENROLL_LATER'
  | 'NOT_INTERESTED'
  | 'NO_SHOW';

export type FollowUpStatus = 'PENDING' | 'COMPLETED' | 'CANCELLED';

export type FollowUpOutcome = 'ENROLLED' | 'POSTPONED' | 'LOST' | 'SCHEDULED_IV';

export interface Child {
  id: number;
  enquiry_id?: string;
  first_name: string;
  last_name?: string;
  dob?: string;
  school?: string;
  interests?: string[];
  notes?: string;
}

export interface Parent {
  id: number;
  name: string;
  phone: string;
  email?: string;
  relationship: string;
  is_primary: boolean;
}

export interface Lead {
  id: number;
  center_id: number;
  child_id: number;
  status: LeadStatus;
  source?: LeadSource;

  // Discovery form fields
  school?: string;
  preferred_schedule?: string;
  parent_expectations?: string[];
  discovery_notes?: string;
  discovery_completed_at?: string;

  // Closure tracking
  closed_reason?: string;
  closed_at?: string;

  // Conversion tracking
  enrollment_id?: number;
  converted_at?: string;

  // Assignment
  assigned_to_user_id?: number;

  created_at: string;
  updated_at: string;

  // Relations (from detail endpoint)
  child?: Child;
}

export interface LeadDetail extends Lead {
  parents?: Parent[];
  intro_visits?: IntroVisit[];
  follow_ups?: FollowUp[];
}

export interface IntroVisit {
  id: number;
  lead_id: number;
  scheduled_at: string;
  attended_at?: string;
  batch_id?: number;
  trainer_user_id?: number;
  outcome?: IVOutcome;
  outcome_notes?: string;
  created_at: string;
  updated_at: string;
}

export interface FollowUp {
  id: number;
  lead_id: number;
  scheduled_date: string;
  completed_at?: string;
  status: FollowUpStatus;
  outcome?: FollowUpOutcome;
  notes?: string;
  assigned_to_user_id?: number;
  created_at: string;
  updated_at: string;
}

// Form types
export interface EnquiryFormData {
  center_id?: number;
  child_first_name: string;
  child_last_name?: string;
  child_dob?: string;
  age?: number;
  gender?: 'Boy' | 'Girl' | 'Other';
  parent_name: string;
  contact_number: string;
  email?: string;
  school?: string;
  source?: LeadSource;
  parent_expectations?: string[];
  preferred_schedule?: string;
  remarks?: string;
  assigned_to_user_id?: number;
}

export interface DiscoveryFormData {
  school?: string;
  preferred_schedule?: string;
  parent_expectations?: string[];
  discovery_notes?: string;
}

export interface IntroVisitFormData {
  lead_id: number;
  scheduled_at: string;
  batch_id?: number;
  trainer_user_id?: number;
}

export interface IntroVisitUpdateData {
  scheduled_at?: string;
  batch_id?: number;
  trainer_user_id?: number;
  attended_at?: string;
  outcome?: IVOutcome;
  outcome_notes?: string;
}

export interface FollowUpFormData {
  lead_id: number;
  scheduled_date: string;
  notes?: string;
  assigned_to_user_id?: number;
}

export interface FollowUpUpdateData {
  scheduled_date?: string;
  completed_at?: string;
  status?: FollowUpStatus;
  outcome?: FollowUpOutcome;
  notes?: string;
  assigned_to_user_id?: number;
}

export interface LeadCloseData {
  reason: string;
}

export interface LeadConvertData {
  enrollment_id: number;
}

// Status configuration
export interface StatusConfig {
  value: LeadStatus;
  label: string;
  color: string;
  description: string;
}

export const STATUS_CONFIGS: Record<LeadStatus, StatusConfig> = {
  ENQUIRY_RECEIVED: {
    value: 'ENQUIRY_RECEIVED',
    label: 'Enquiry',
    color: 'bg-blue-100 text-blue-800 border-blue-300',
    description: 'New enquiry received'
  },
  DISCOVERY_COMPLETED: {
    value: 'DISCOVERY_COMPLETED',
    label: 'Discovery',
    color: 'bg-indigo-100 text-indigo-800 border-indigo-300',
    description: 'Discovery form completed'
  },
  IV_SCHEDULED: {
    value: 'IV_SCHEDULED',
    label: 'IV Scheduled',
    color: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    description: 'Intro visit scheduled'
  },
  IV_COMPLETED: {
    value: 'IV_COMPLETED',
    label: 'IV Done',
    color: 'bg-purple-100 text-purple-800 border-purple-300',
    description: 'Intro visit completed'
  },
  IV_NO_SHOW: {
    value: 'IV_NO_SHOW',
    label: 'No Show',
    color: 'bg-gray-100 text-gray-800 border-gray-300',
    description: 'Did not attend intro visit'
  },
  FOLLOW_UP_PENDING: {
    value: 'FOLLOW_UP_PENDING',
    label: 'Follow Up',
    color: 'bg-orange-100 text-orange-800 border-orange-300',
    description: 'Follow-up required'
  },
  CONVERTED: {
    value: 'CONVERTED',
    label: 'Converted',
    color: 'bg-green-100 text-green-800 border-green-300',
    description: 'Converted to enrollment'
  },
  CLOSED_LOST: {
    value: 'CLOSED_LOST',
    label: 'Lost',
    color: 'bg-red-100 text-red-800 border-red-300',
    description: 'Lead closed/lost'
  },
};

export const PARENT_EXPECTATIONS = [
  'child_development',
  'physical_activity',
  'socialization_skills',
  'confidence_building',
  'motor_skills',
  'fun_recreation',
  'structured_program',
  'experienced_trainers',
];

export const IV_OUTCOME_LABELS: Record<IVOutcome, string> = {
  INTERESTED_ENROLL_NOW: 'Interested - Enroll Now',
  INTERESTED_ENROLL_LATER: 'Interested - Enroll Later',
  NOT_INTERESTED: 'Not Interested',
  NO_SHOW: 'No Show',
};

export const FOLLOW_UP_OUTCOME_LABELS: Record<FollowUpOutcome, string> = {
  ENROLLED: 'Enrolled',
  POSTPONED: 'Postponed',
  LOST: 'Lost',
  SCHEDULED_IV: 'Scheduled IV',
};

// Pagination types
export interface PaginatedLeadsResponse {
  leads: Lead[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
