import { useContext } from 'react';
import { CenterContext } from '@/contexts/CenterContext';

export function useCenterContext() {
  const context = useContext(CenterContext);

  if (!context) {
    throw new Error('useCenterContext must be used within CenterContextProvider');
  }

  return context;
}
