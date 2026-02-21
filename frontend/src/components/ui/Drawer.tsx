'use client';

import { ReactNode, useEffect } from 'react';
import { X } from 'lucide-react';

interface DrawerProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  noPadding?: boolean;
}

export default function Drawer({ open, onClose, title, children, size = 'md', noPadding = false }: DrawerProps) {
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) onClose();
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [open, onClose]);

  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => { document.body.style.overflow = 'unset'; };
  }, [open]);

  if (!open) return null;

  const sizeClasses = {
    sm: 'w-[400px]',
    md: 'w-[500px]',
    lg: 'w-[700px]',
    xl: 'w-[900px]',
  };

  return (
    <>
      <div className="modal-backdrop" onClick={onClose} />
      <div className={`fixed right-0 top-0 h-full ${sizeClasses[size]} bg-white shadow-2xl z-50 flex flex-col animate-slide-in-right rounded-l-2xl`}>
        <div className="modal-header">
          <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
          <button
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Close drawer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className={`flex-1 overflow-y-auto ${noPadding ? '' : 'p-6'}`}>
          {children}
        </div>
      </div>
    </>
  );
}
