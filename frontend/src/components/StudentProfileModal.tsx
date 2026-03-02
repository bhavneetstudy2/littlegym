'use client';

import StudentProfileContent from './StudentProfileContent';

interface StudentProfileModalProps {
  childId: number;
  enrollmentId?: number;
  centerId: number;
  userRole?: string;
  onClose: () => void;
}

export default function StudentProfileModal({ childId, enrollmentId, centerId, userRole, onClose }: StudentProfileModalProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <StudentProfileContent
          childId={childId}
          enrollmentId={enrollmentId}
          centerId={centerId}
          userRole={userRole}
          onClose={onClose}
        />
      </div>
    </div>
  );
}
