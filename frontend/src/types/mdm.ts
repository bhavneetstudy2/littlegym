// Master Data Management type definitions

export interface ClassType {
  id: number;
  name: string;
  description: string | null;
  age_min: number;
  age_max: number;
  duration_minutes: number;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Curriculum {
  id: number;
  name: string;
  level: string | null;
  age_min: number | null;
  age_max: number | null;
  description: string | null;
  center_id: number | null;
  is_global: boolean;
  active: boolean;
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

export interface BatchMapping {
  id: number;
  batch_id: number;
  class_type_id: number | null;
  curriculum_id: number | null;
  center_id: number;
  created_at: string;
  updated_at: string;
}
