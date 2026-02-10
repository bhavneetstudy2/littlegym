'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useCenter } from '@/contexts/CenterContext';
import { api } from '@/lib/api';

interface Child {
  id: number;
  first_name: string;
  last_name?: string;
  dob?: string;
  school?: string;
  interests?: string[];
  notes?: string;
}

interface Parent {
  id: number;
  name: string;
  phone: string;
  email?: string;
  relationship_type?: string;
  is_primary_contact: boolean;
}

interface BatchInfo {
  id: number;
  name: string;
  age_min?: number;
  age_max?: number;
  days_of_week?: string[];
  start_time?: string;
  end_time?: string;
}

interface EnrolledStudent {
  enrollment_id: number;
  plan_type: string;
  status: string;
  start_date?: string;
  end_date?: string;
  visits_included?: number;
  visits_used: number;
  days_selected?: string[];
  enrollment_notes?: string;
  enrolled_at: string;
  child: Child;
  parents: Parent[];
  batch?: BatchInfo;
  total_paid: number;
  total_discount: number;
}

interface AttendanceRecord {
  id: number;
  class_session_id: number;
  child_id: number;
  status: string;
  marked_at?: string;
  notes?: string;
  created_at: string;
}

interface SkillProgress {
  id: number;
  skill_id: number;
  skill_name: string;
  category?: string;
  level: string;
  last_updated_at?: string;
  notes?: string;
}

// Helpers
const formatDate = (dateString?: string) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  });
};

const formatDateTime = (dateString?: string) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const calculateAge = (dob?: string) => {
  if (!dob) return null;
  const today = new Date();
  const birthDate = new Date(dob);
  let age = today.getFullYear() - birthDate.getFullYear();
  const m = today.getMonth() - birthDate.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }
  return age;
};

const getStatusBadge = (status: string) => {
  const styles: Record<string, string> = {
    'ACTIVE': 'bg-green-100 text-green-800',
    'EXPIRED': 'bg-red-100 text-red-800',
    'PAUSED': 'bg-yellow-100 text-yellow-800',
    'CANCELLED': 'bg-gray-100 text-gray-800',
    'PRESENT': 'bg-green-100 text-green-800',
    'ABSENT': 'bg-red-100 text-red-800',
    'MAKEUP': 'bg-yellow-100 text-yellow-800',
    'TRIAL': 'bg-blue-100 text-blue-800',
  };
  return styles[status] || 'bg-gray-100 text-gray-800';
};

const getSkillLevelBadge = (level: string) => {
  const styles: Record<string, string> = {
    'NOT_STARTED': 'bg-gray-100 text-gray-600',
    'IN_PROGRESS': 'bg-yellow-100 text-yellow-800',
    'ACHIEVED': 'bg-blue-100 text-blue-800',
    'MASTERED': 'bg-green-100 text-green-800',
  };
  return styles[level] || 'bg-gray-100 text-gray-800';
};

const getPlanDisplay = (planType: string) => {
  const types: Record<string, string> = {
    'PAY_PER_VISIT': 'Per Visit',
    'WEEKLY': 'Weekly',
    'MONTHLY': 'Monthly',
    'QUARTERLY': 'Quarterly',
    'YEARLY': 'Yearly',
    'CUSTOM': 'Custom'
  };
  return types[planType] || planType;
};

export default function StudentProfilePage() {
  const router = useRouter();
  const params = useParams();
  const { selectedCenter } = useCenter();
  const childId = params.id as string;

  const [student, setStudent] = useState<EnrolledStudent | null>(null);
  const [attendance, setAttendance] = useState<AttendanceRecord[]>([]);
  const [skillProgress, setSkillProgress] = useState<SkillProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'attendance' | 'progress'>('overview');

  useEffect(() => {
    if (selectedCenter && childId) {
      fetchStudentData();
    }
  }, [selectedCenter, childId]);

  const fetchStudentData = async () => {
    if (!selectedCenter) return;

    setLoading(true);
    setError(null);

    try {
      // Fetch all enrolled students and find the one with matching child_id
      const studentsRes = await api.get<EnrolledStudent[]>(
        `/api/v1/enrollments/students?center_id=${selectedCenter.id}`
      );

      const matchingStudent = studentsRes.find(s => s.child.id === parseInt(childId));
      if (matchingStudent) {
        setStudent(matchingStudent);
      } else {
        setError('Student not found');
      }

      // Fetch attendance history
      try {
        const attendanceRes = await api.get<AttendanceRecord[]>(
          `/api/v1/attendance/children/${childId}`
        );
        setAttendance(attendanceRes);
      } catch (err) {
        console.error('Failed to load attendance:', err);
      }

      // Fetch skill progress
      try {
        const progressRes = await api.get<SkillProgress[]>(
          `/api/v1/curriculum/progress/children/${childId}`
        );
        setSkillProgress(progressRes);
      } catch (err) {
        console.error('Failed to load skill progress:', err);
      }

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load student data');
    } finally {
      setLoading(false);
    }
  };

  if (!selectedCenter) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500 mb-4">Please select a center first</p>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading student profile...</p>
        </div>
      </div>
    );
  }

  if (error || !student) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error || 'Student not found'}</p>
          <button
            onClick={() => router.push('/students')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to Students
          </button>
        </div>
      </div>
    );
  }

  const age = calculateAge(student.child.dob);
  const primaryParent = student.parents.find(p => p.is_primary_contact) || student.parents[0];

  // Calculate attendance stats
  const presentCount = attendance.filter(a => a.status === 'PRESENT').length;
  const absentCount = attendance.filter(a => a.status === 'ABSENT').length;
  const totalSessions = attendance.length;
  const attendanceRate = totalSessions > 0 ? Math.round((presentCount / totalSessions) * 100) : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <button
                onClick={() => router.push('/students')}
                className="mr-3 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  {student.child.first_name} {student.child.last_name || ''}
                </h1>
                <p className="text-sm text-gray-500">
                  {age ? `${age} years` : ''} {student.batch ? `| ${student.batch.name}` : ''}
                </p>
              </div>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBadge(student.status)}`}>
              {student.status}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 mt-4">
        <div className="border-b border-gray-200">
          <nav className="flex gap-4">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'overview'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('attendance')}
              className={`py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'attendance'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Attendance ({totalSessions})
            </button>
            <button
              onClick={() => setActiveTab('progress')}
              className={`py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'progress'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Progress ({skillProgress.length})
            </button>
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-lg shadow p-4">
                <div className="text-sm text-gray-500">Classes Booked</div>
                <div className="text-2xl font-bold text-blue-600">{student.visits_included || '-'}</div>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <div className="text-sm text-gray-500">Classes Attended</div>
                <div className="text-2xl font-bold text-green-600">{student.visits_used}</div>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <div className="text-sm text-gray-500">Classes Remaining</div>
                <div className="text-2xl font-bold text-orange-600">
                  {student.visits_included ? student.visits_included - student.visits_used : '-'}
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <div className="text-sm text-gray-500">Attendance Rate</div>
                <div className="text-2xl font-bold text-purple-600">{attendanceRate}%</div>
              </div>
            </div>

            {/* Child Information */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Child Information</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-gray-500 text-sm">Full Name</span>
                  <p className="font-medium">{student.child.first_name} {student.child.last_name || ''}</p>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Date of Birth</span>
                  <p className="font-medium">{student.child.dob ? `${formatDate(student.child.dob)} (${age} years)` : '-'}</p>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">School</span>
                  <p className="font-medium">{student.child.school || '-'}</p>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Interests</span>
                  <p className="font-medium">{student.child.interests?.join(', ') || '-'}</p>
                </div>
                {student.child.notes && (
                  <div className="col-span-2">
                    <span className="text-gray-500 text-sm">Notes</span>
                    <p className="font-medium">{student.child.notes}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Parent Information */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Parent/Guardian Information</h2>
              <div className="space-y-4">
                {student.parents.map((parent, idx) => (
                  <div key={idx} className="bg-gray-50 p-4 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-semibold">{parent.name}</span>
                      {parent.is_primary_contact && (
                        <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded">Primary</span>
                      )}
                      {parent.relationship_type && (
                        <span className="text-gray-500 text-sm">({parent.relationship_type})</span>
                      )}
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-gray-500">Phone:</span>{' '}
                        <a href={`tel:${parent.phone}`} className="text-blue-600 font-medium">{parent.phone}</a>
                      </div>
                      <div>
                        <span className="text-gray-500">Email:</span>{' '}
                        <span className="font-medium">{parent.email || '-'}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Enrollment Information */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Enrollment Details</h2>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div>
                  <span className="text-gray-500 text-sm">Plan Type</span>
                  <p className="font-medium">
                    <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-sm">
                      {getPlanDisplay(student.plan_type)}
                    </span>
                  </p>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Batch</span>
                  <p className="font-medium">
                    {student.batch ? (
                      <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-sm">
                        {student.batch.name}
                      </span>
                    ) : '-'}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Days Selected</span>
                  <p className="font-medium">{student.days_selected?.join(', ') || '-'}</p>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Start Date</span>
                  <p className="font-medium">{formatDate(student.start_date)}</p>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">End Date</span>
                  <p className="font-medium">{formatDate(student.end_date)}</p>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Enrolled On</span>
                  <p className="font-medium">{formatDate(student.enrolled_at)}</p>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Total Paid</span>
                  <p className="font-medium text-green-600">Rs.{student.total_paid.toLocaleString()}</p>
                </div>
                {student.total_discount > 0 && (
                  <div>
                    <span className="text-gray-500 text-sm">Discount Applied</span>
                    <p className="font-medium text-orange-600">Rs.{student.total_discount.toLocaleString()}</p>
                  </div>
                )}
              </div>
              {student.enrollment_notes && (
                <div className="mt-4 pt-4 border-t">
                  <span className="text-gray-500 text-sm">Notes</span>
                  <p className="font-medium">{student.enrollment_notes}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'attendance' && (
          <div className="bg-white rounded-lg shadow">
            {/* Attendance Summary */}
            <div className="p-4 border-b bg-gray-50">
              <div className="flex gap-6">
                <div>
                  <span className="text-gray-500 text-sm">Total Sessions:</span>{' '}
                  <span className="font-semibold">{totalSessions}</span>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Present:</span>{' '}
                  <span className="font-semibold text-green-600">{presentCount}</span>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Absent:</span>{' '}
                  <span className="font-semibold text-red-600">{absentCount}</span>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Rate:</span>{' '}
                  <span className="font-semibold text-purple-600">{attendanceRate}%</span>
                </div>
              </div>
            </div>

            {/* Attendance Table */}
            {attendance.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No attendance records found
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="text-left p-3 font-semibold text-gray-700">#</th>
                      <th className="text-left p-3 font-semibold text-gray-700">Date & Time</th>
                      <th className="text-center p-3 font-semibold text-gray-700">Status</th>
                      <th className="text-left p-3 font-semibold text-gray-700">Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {attendance.map((record, idx) => (
                      <tr key={record.id} className="border-b hover:bg-gray-50">
                        <td className="p-3 text-gray-500">{idx + 1}</td>
                        <td className="p-3">
                          {formatDateTime(record.marked_at || record.created_at)}
                        </td>
                        <td className="p-3 text-center">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusBadge(record.status)}`}>
                            {record.status}
                          </span>
                        </td>
                        <td className="p-3 text-gray-600 text-sm">{record.notes || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {activeTab === 'progress' && (
          <div className="bg-white rounded-lg shadow">
            {skillProgress.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No skill progress recorded yet
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="text-left p-3 font-semibold text-gray-700">#</th>
                      <th className="text-left p-3 font-semibold text-gray-700">Skill</th>
                      <th className="text-left p-3 font-semibold text-gray-700">Category</th>
                      <th className="text-center p-3 font-semibold text-gray-700">Level</th>
                      <th className="text-left p-3 font-semibold text-gray-700">Last Updated</th>
                      <th className="text-left p-3 font-semibold text-gray-700">Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {skillProgress.map((progress, idx) => (
                      <tr key={progress.id} className="border-b hover:bg-gray-50">
                        <td className="p-3 text-gray-500">{idx + 1}</td>
                        <td className="p-3 font-medium">{progress.skill_name}</td>
                        <td className="p-3 text-gray-600">{progress.category || '-'}</td>
                        <td className="p-3 text-center">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getSkillLevelBadge(progress.level)}`}>
                            {progress.level.replace('_', ' ')}
                          </span>
                        </td>
                        <td className="p-3 text-gray-600 text-sm">
                          {formatDateTime(progress.last_updated_at)}
                        </td>
                        <td className="p-3 text-gray-600 text-sm">{progress.notes || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
