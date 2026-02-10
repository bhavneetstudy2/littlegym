'use client';

import { createContext, useContext, useState, ReactNode } from 'react';

interface StudentLookupContextType {
  isLookupOpen: boolean;
  openLookup: () => void;
  closeLookup: () => void;
}

const StudentLookupContext = createContext<StudentLookupContextType>({
  isLookupOpen: false,
  openLookup: () => {},
  closeLookup: () => {},
});

export function StudentLookupProvider({ children }: { children: ReactNode }) {
  const [isLookupOpen, setIsLookupOpen] = useState(false);

  return (
    <StudentLookupContext.Provider
      value={{
        isLookupOpen,
        openLookup: () => setIsLookupOpen(true),
        closeLookup: () => setIsLookupOpen(false),
      }}
    >
      {children}
    </StudentLookupContext.Provider>
  );
}

export function useStudentLookup() {
  return useContext(StudentLookupContext);
}
