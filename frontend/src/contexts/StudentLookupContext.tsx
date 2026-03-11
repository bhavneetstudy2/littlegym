'use client';

import { createContext, useContext, useState, ReactNode } from 'react';

interface StudentLookupContextType {
  isLookupOpen: boolean;
  initialChildId: number | null;
  openLookup: () => void;
  openLookupWithChild: (childId: number) => void;
  closeLookup: () => void;
}

const StudentLookupContext = createContext<StudentLookupContextType>({
  isLookupOpen: false,
  initialChildId: null,
  openLookup: () => {},
  openLookupWithChild: () => {},
  closeLookup: () => {},
});

export function StudentLookupProvider({ children }: { children: ReactNode }) {
  const [isLookupOpen, setIsLookupOpen] = useState(false);
  const [initialChildId, setInitialChildId] = useState<number | null>(null);

  return (
    <StudentLookupContext.Provider
      value={{
        isLookupOpen,
        initialChildId,
        openLookup: () => { setInitialChildId(null); setIsLookupOpen(true); },
        openLookupWithChild: (childId: number) => { setInitialChildId(childId); setIsLookupOpen(true); },
        closeLookup: () => { setIsLookupOpen(false); setInitialChildId(null); },
      }}
    >
      {children}
    </StudentLookupContext.Provider>
  );
}

export function useStudentLookup() {
  return useContext(StudentLookupContext);
}
