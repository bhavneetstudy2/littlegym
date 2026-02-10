'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface Child {
  id: number;
  enquiry_id?: string;
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
  session_date?: string;
  batch_id?: number;
  batch_name?: string;
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

interface StudentProfileContentProps {
  childId: number;
  enrollmentId?: number;
  centerId: number;
  onClose?: () => void;
  onBack?: () => void;
}

export default function StudentProfileContent({ childId, centerId, onClose, onBack }: StudentProfileContentProps) {
  const [allEnrollments, setAllEnrollments] = useState<EnrolledStudent[]>([]);
  const [childInfo, setChildInfo] = useState<Child | null>(null);
  const [parents, setParents] = useState<Parent[]>([]);
  const [attendance, setAttendance] = useState<AttendanceRecord[]>([]);
  const [skillProgress, setSkillProgress] = useState<SkillProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'attendance' | 'progress'>('overview');

  useEffect(() => {
    if (childId && centerId) {
      fetchStudentData();
    }
  }, [childId, centerId]);

  const fetchStudentData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch only this child's enrollments (not all students)
      const childEnrollments = await api.get<EnrolledStudent[]>(
        `/api/v1/enrollments/students?center_id=${centerId}&child_id=${childId}&limit=100`
      );

      if (childEnrollments.length > 0) {
        // Sort: ACTIVE first, then by enrolled_at descending
        const statusOrder: Record<string, number> = { 'ACTIVE': 0, 'PAUSED': 1, 'EXPIRED': 2, 'CANCELLED': 3 };
        childEnrollments.sort((a, b) => {
          const orderA = statusOrder[a.status] ?? 99;
          const orderB = statusOrder[b.status] ?? 99;
          if (orderA !== orderB) return orderA - orderB;
          return new Date(b.enrolled_at).getTime() - new Date(a.enrolled_at).getTime();
        });

        setAllEnrollments(childEnrollments);
        setChildInfo(childEnrollments[0].child);
        setParents(childEnrollments[0].parents);
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

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading student profile...</p>
      </div>
    );
  }

  if (error || !childInfo || allEnrollments.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <p className="text-red-500 mb-4">{error || 'Student not found'}</p>
        {onClose && (
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Close
          </button>
        )}
        {onBack && (
          <button
            onClick={onBack}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            Back to search
          </button>
        )}
      </div>
    );
  }

  const age = calculateAge(childInfo.dob);
  const primaryParent = parents.find(p => p.is_primary_contact) || parents[0];

  // Group attendance by batch
  const attendanceByBatch: Record<string, AttendanceRecord[]> = {};
  for (const record of attendance) {
    const batchKey = record.batch_name || 'Unknown Batch';
    if (!attendanceByBatch[batchKey]) {
      attendanceByBatch[batchKey] = [];
    }
    attendanceByBatch[batchKey].push(record);
  }

  // Overall attendance stats
  const totalPresent = attendance.filter(a => a.status === 'PRESENT').length;
  const totalAbsent = attendance.filter(a => a.status === 'ABSENT').length;
  const totalSessions = attendance.length;
  const overallRate = totalSessions > 0 ? Math.round((totalPresent / totalSessions) * 100) : 0;

  // Total stats across all enrollments
  const totalBooked = allEnrollments.reduce((sum, e) => sum + (e.visits_included || 0), 0);
  const totalAttended = allEnrollments.reduce((sum, e) => sum + (e.visits_used || 0), 0);
  const totalRemaining = allEnrollments.reduce((sum, e) => sum + Math.max(0, (e.visits_included || 0) - (e.visits_used || 0)), 0);
  const activeEnrollments = allEnrollments.filter(e => e.status === 'ACTIVE');

  return (
    <>
      {/* Header */}
      <div className="bg-white border-b p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {onBack && (
              <button
                onClick={onBack}
                className="text-gray-400 hover:text-gray-600 transition"
                title="Back to search"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
            )}
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                {childInfo.first_name} {childInfo.last_name || ''}
                {childInfo.enquiry_id && (
                  <span className="ml-2 text-sm font-normal text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                    {childInfo.enquiry_id}
                  </span>
                )}
              </h2>
              <p className="text-sm text-gray-500">
                {age ? `${age} years` : ''}
                {primaryParent ? ` | ${primaryParent.name} (${primaryParent.phone})` : ''}
                {` | ${allEnrollments.length} enrollment${allEnrollments.length > 1 ? 's' : ''}`}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {activeEnrollments.length > 0 && (
              <span className="px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                {activeEnrollments.length} Active
              </span>
            )}
            {allEnrollments.filter(e => e.status === 'EXPIRED').length > 0 && (
              <span className="px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                {allEnrollments.filter(e => e.status === 'EXPIRED').length} Expired
              </span>
            )}
            {onClose && (
              <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl ml-2">
                &times;
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b bg-white px-4">
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

      {/* Content */}
      <div className="flex-1 overflow-auto p-6 bg-gray-50">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-white rounded-lg shadow p-4">
                <div className="text-sm text-gray-500">Total Booked</div>
                <div className="text-2xl font-bold text-blue-600">{totalBooked || '-'}</div>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <div className="text-sm text-gray-500">Total Attended</div>
                <div className="text-2xl font-bold text-green-600">{totalAttended}</div>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <div className="text-sm text-gray-500">Remaining (Active)</div>
                <div className="text-2xl font-bold text-orange-600">{totalRemaining || '-'}</div>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <div className="text-sm text-gray-500">Attendance Rate</div>
                <div className="text-2xl font-bold text-purple-600">{overallRate}%</div>
              </div>
              <div className="bg-white rounded-lg shadow p-4">
                <div className="text-sm text-gray-500">Enrollments</div>
                <div className="text-2xl font-bold text-indigo-600">{allEnrollments.length}</div>
              </div>
            </div>

            {/* Child Information */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Child Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-gray-500 text-sm">Full Name</span>
                  <p className="font-medium">{childInfo.first_name} {childInfo.last_name || ''}</p>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">TLG ID / Enquiry ID</span>
                  <p className="font-medium text-blue-600">{childInfo.enquiry_id || '-'}</p>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Date of Birth</span>
                  <p className="font-medium">{childInfo.dob ? `${formatDate(childInfo.dob)} (${age} years)` : '-'}</p>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">School</span>
                  <p className="font-medium">{childInfo.school || '-'}</p>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Interests</span>
                  <p className="font-medium">{childInfo.interests?.join(', ') || '-'}</p>
                </div>
                {childInfo.notes && (
                  <div className="col-span-2">
                    <span className="text-gray-500 text-sm">Notes</span>
                    <p className="font-medium">{childInfo.notes}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Parent Information */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">Parent/Guardian Information</h3>
              <div className="space-y-4">
                {parents.map((parent, idx) => (
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

            {/* Enrollment History - ALL enrollments */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">
                Enrollment History ({allEnrollments.length})
              </h3>
              <div className="space-y-4">
                {allEnrollments.map((enrollment) => {
                  const remaining = Math.max(0, (enrollment.visits_included || 0) - (enrollment.visits_used || 0));
                  const isActive = enrollment.status === 'ACTIVE';

                  return (
                    <div
                      key={enrollment.enrollment_id}
                      className={`border rounded-lg p-4 ${isActive ? 'border-green-300 bg-green-50' : 'border-gray-200 bg-gray-50'}`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-gray-900">
                            {enrollment.batch?.name || 'No Batch'}
                          </span>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStatusBadge(enrollment.status)}`}>
                            {enrollment.status}
                          </span>
                          <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">
                            {getPlanDisplay(enrollment.plan_type)}
                          </span>
                        </div>
                        <div className="text-sm text-gray-500">
                          #{enrollment.enrollment_id}
                        </div>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                        <div>
                          <span className="text-gray-500">Period:</span>{' '}
                          <span className="font-medium">
                            {formatDate(enrollment.start_date)} - {formatDate(enrollment.end_date)}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500">Booked:</span>{' '}
                          <span className="font-medium">{enrollment.visits_included || '-'}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Attended:</span>{' '}
                          <span className="font-medium text-green-700">{enrollment.visits_used}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Remaining:</span>{' '}
                          <span className={`font-medium ${remaining === 0 && isActive ? 'text-red-600' : 'text-orange-600'}`}>
                            {remaining}
                          </span>
                        </div>
                      </div>

                      {(enrollment.total_paid > 0 || enrollment.total_discount > 0) && (
                        <div className="mt-2 pt-2 border-t border-gray-200 flex gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">Paid:</span>{' '}
                            <span className="font-medium text-green-600">Rs.{enrollment.total_paid.toLocaleString()}</span>
                          </div>
                          {enrollment.total_discount > 0 && (
                            <div>
                              <span className="text-gray-500">Discount:</span>{' '}
                              <span className="font-medium text-orange-600">Rs.{enrollment.total_discount.toLocaleString()}</span>
                            </div>
                          )}
                        </div>
                      )}

                      {enrollment.enrollment_notes && (
                        <div className="mt-2 pt-2 border-t border-gray-200 text-sm">
                          <span className="text-gray-500">Notes:</span>{' '}
                          <span className="text-gray-700">{enrollment.enrollment_notes}</span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'attendance' && (
          <div className="space-y-6">
            {/* Overall Attendance Summary */}
            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex gap-6">
                <div>
                  <span className="text-gray-500 text-sm">Total Sessions:</span>{' '}
                  <span className="font-semibold">{totalSessions}</span>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Present:</span>{' '}
                  <span className="font-semibold text-green-600">{totalPresent}</span>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Absent:</span>{' '}
                  <span className="font-semibold text-red-600">{totalAbsent}</span>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Rate:</span>{' '}
                  <span className="font-semibold text-purple-600">{overallRate}%</span>
                </div>
              </div>
            </div>

            {/* Attendance grouped by batch */}
            {Object.keys(attendanceByBatch).length === 0 ? (
              <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
                No attendance records found
              </div>
            ) : (
              Object.entries(attendanceByBatch).map(([batchName, records]) => {
                const batchPresent = records.filter(r => r.status === 'PRESENT').length;
                const batchAbsent = records.filter(r => r.status === 'ABSENT').length;
                const batchRate = records.length > 0 ? Math.round((batchPresent / records.length) * 100) : 0;

                // Find matching enrollment for this batch
                const matchingEnrollment = allEnrollments.find(e => e.batch?.name === batchName);

                return (
                  <div key={batchName} className="bg-white rounded-lg shadow">
                    {/* Batch header */}
                    <div className="p-4 border-b bg-gray-50 rounded-t-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold text-gray-900">{batchName}</h4>
                          {matchingEnrollment && (
                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStatusBadge(matchingEnrollment.status)}`}>
                              {matchingEnrollment.status}
                            </span>
                          )}
                        </div>
                        <div className="flex gap-4 text-sm">
                          <span>Sessions: <strong>{records.length}</strong></span>
                          <span className="text-green-600">Present: <strong>{batchPresent}</strong></span>
                          <span className="text-red-600">Absent: <strong>{batchAbsent}</strong></span>
                          <span className="text-purple-600">Rate: <strong>{batchRate}%</strong></span>
                        </div>
                      </div>
                    </div>

                    {/* Attendance table for this batch */}
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="text-left p-3 font-semibold text-gray-700 w-12">#</th>
                            <th className="text-left p-3 font-semibold text-gray-700">Session Date</th>
                            <th className="text-center p-3 font-semibold text-gray-700">Status</th>
                            <th className="text-left p-3 font-semibold text-gray-700">Notes</th>
                          </tr>
                        </thead>
                        <tbody>
                          {records.map((record, idx) => (
                            <tr key={record.id} className="border-b hover:bg-gray-50">
                              <td className="p-3 text-gray-500">{idx + 1}</td>
                              <td className="p-3">
                                {formatDate(record.session_date) || formatDate(record.marked_at) || '-'}
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
                  </div>
                );
              })
            )}
          </div>
        )}

        {activeTab === 'progress' && (
          <div className="space-y-4">
            {skillProgress.length === 0 ? (
              <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
                No skill progress recorded yet
              </div>
            ) : (
              <>
                {/* Progress Summary Header */}
                <div className="bg-white rounded-lg shadow p-4">
                  <div className="flex items-center gap-6">
                    <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center">
                      <svg className="w-10 h-10 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                      </svg>
                    </div>
                    <div className="flex-1">
                      <div className="flex flex-wrap gap-6 text-sm">
                        <div>
                          <span className="text-gray-500">Skills Mastered:</span>{' '}
                          <span className="font-semibold">
                            {skillProgress.filter(s => s.level === 'MASTERED').length} / {skillProgress.length}
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <span className="text-gray-500">Overall Progress:</span>{' '}
                          {[1, 2, 3, 4, 5].map((star) => {
                            const mastered = skillProgress.filter(s => s.level === 'MASTERED').length;
                            const achieved = skillProgress.filter(s => s.level === 'ACHIEVED').length;
                            const total = skillProgress.length;
                            const progress = total > 0 ? ((mastered * 2 + achieved) / (total * 2)) * 5 : 0;
                            return (
                              <svg
                                key={star}
                                className={`w-5 h-5 ${star <= Math.round(progress) ? 'text-yellow-400' : 'text-gray-300'}`}
                                fill="currentColor"
                                viewBox="0 0 24 24"
                              >
                                <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/>
                              </svg>
                            );
                          })}
                        </div>
                        <div>
                          <span className="text-gray-500">Last Updated:</span>{' '}
                          <span className="font-semibold">
                            {skillProgress.length > 0
                              ? formatDate(skillProgress.reduce((latest, s) =>
                                  !latest || (s.last_updated_at && s.last_updated_at > latest) ? s.last_updated_at : latest,
                                  skillProgress[0].last_updated_at
                                ))
                              : '-'
                            }
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Skills grouped by category */}
                {(() => {
                  // Group skills by category
                  const groupedSkills: Record<string, typeof skillProgress> = {};
                  skillProgress.forEach(skill => {
                    const category = skill.category || 'General';
                    if (!groupedSkills[category]) groupedSkills[category] = [];
                    groupedSkills[category].push(skill);
                  });

                  return Object.entries(groupedSkills).map(([category, skills]) => (
                    <div key={category} className="bg-white rounded-lg shadow">
                      {/* Category Header */}
                      <div className="p-4 border-b bg-gray-50 rounded-t-lg flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <input type="checkbox" className="w-4 h-4 text-blue-600 rounded" readOnly />
                          <h4 className="font-semibold text-gray-900">{category} ({skills.length})</h4>
                        </div>
                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>

                      {/* Skills in this category */}
                      <div className="divide-y">
                        {skills.map((skill) => (
                          <div key={skill.id} className="p-4">
                            <div className="flex items-center justify-between mb-2">
                              <h5 className="font-medium text-gray-900">{skill.skill_name}</h5>
                              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                              </svg>
                            </div>

                            {/* Level buttons */}
                            <div className="flex gap-2 mb-3">
                              {['NOT_STARTED', 'IN_PROGRESS', 'ACHIEVED', 'MASTERED'].map((level) => {
                                const isActive = skill.level === level;
                                const labels: Record<string, string> = {
                                  'NOT_STARTED': 'Not Started',
                                  'IN_PROGRESS': 'Learning',
                                  'ACHIEVED': 'Developing',
                                  'MASTERED': 'Mastered'
                                };
                                return (
                                  <div
                                    key={level}
                                    className={`px-3 py-1.5 rounded-full text-sm flex items-center gap-1 ${
                                      isActive
                                        ? level === 'MASTERED'
                                          ? 'bg-green-100 text-green-800 border-2 border-green-500'
                                          : level === 'ACHIEVED'
                                          ? 'bg-blue-100 text-blue-800 border-2 border-blue-500'
                                          : level === 'IN_PROGRESS'
                                          ? 'bg-yellow-100 text-yellow-800 border-2 border-yellow-500'
                                          : 'bg-gray-100 text-gray-600 border-2 border-gray-400'
                                        : 'bg-gray-50 text-gray-500 border border-gray-200'
                                    }`}
                                  >
                                    {isActive && (
                                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                      </svg>
                                    )}
                                    {labels[level]}
                                  </div>
                                );
                              })}
                            </div>

                            {/* Notes and last update */}
                            {skill.notes && (
                              <div className="text-sm text-gray-600 italic mb-1">
                                Coach Note: &quot;{skill.notes}&quot;
                              </div>
                            )}
                            <div className="text-xs text-gray-400">
                              Last Update: {formatDate(skill.last_updated_at)}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ));
                })()}
              </>
            )}
          </div>
        )}
      </div>
    </>
  );
}
