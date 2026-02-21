'use client';

import { useState, useEffect } from 'react';
import { convertDDMMYYYYtoISO, convertISOtoDDMMYYYY } from '@/lib/utils';

interface DateInputProps {
  value?: string; // Expected in yyyy-mm-dd (ISO) format
  onChange: (isoDate: string) => void; // Returns yyyy-mm-dd (ISO) format
  placeholder?: string;
  className?: string;
  required?: boolean;
  disabled?: boolean;
  min?: string; // yyyy-mm-dd format
  max?: string; // yyyy-mm-dd format
  label?: string;
}

/**
 * Date input component that accepts and displays dates in dd/mm/yyyy format
 * while internally working with yyyy-mm-dd (ISO) format for API compatibility
 */
export default function DateInput({
  value = '',
  onChange,
  placeholder = 'dd/mm/yyyy',
  className = '',
  required = false,
  disabled = false,
  min,
  max,
  label,
}: DateInputProps) {
  const [displayValue, setDisplayValue] = useState('');
  const [error, setError] = useState('');

  // Convert incoming ISO value to dd/mm/yyyy for display
  useEffect(() => {
    if (value) {
      setDisplayValue(convertISOtoDDMMYYYY(value));
    } else {
      setDisplayValue('');
    }
  }, [value]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const input = e.target.value;
    setDisplayValue(input);
    setError('');

    // Only validate and convert when we have a complete date
    if (input.length === 10) {
      const isoDate = convertDDMMYYYYtoISO(input);

      if (!isoDate) {
        setError('Invalid date format. Use dd/mm/yyyy');
        return;
      }

      // Validate min/max
      if (min && isoDate < min) {
        const minDisplay = convertISOtoDDMMYYYY(min);
        setError(`Date must be on or after ${minDisplay}`);
        return;
      }

      if (max && isoDate > max) {
        const maxDisplay = convertISOtoDDMMYYYY(max);
        setError(`Date must be on or before ${maxDisplay}`);
        return;
      }

      // Valid date - call onChange with ISO format
      onChange(isoDate);
    } else if (input.length === 0) {
      // Clear value
      onChange('');
    }
  };

  const handleBlur = () => {
    // Format incomplete input on blur
    if (displayValue && displayValue.length < 10) {
      setError('Please enter a complete date (dd/mm/yyyy)');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    // Auto-add slashes
    const input = (e.target as HTMLInputElement).value;

    // Add slash after day (2 digits)
    if (input.length === 2 && !input.includes('/') && e.key !== 'Backspace') {
      setDisplayValue(input + '/');
    }

    // Add slash after month (5 chars = dd/mm)
    if (input.length === 5 && input.split('/').length === 2 && e.key !== 'Backspace') {
      setDisplayValue(input + '/');
    }
  };

  return (
    <div className="w-full">
      {label && (
        <label className="input-label">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <input
        type="text"
        value={displayValue}
        onChange={handleChange}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        required={required}
        maxLength={10}
        className={`input ${error ? 'border-red-500 focus:ring-red-500 focus:border-red-500' : ''} ${className}`}
      />
      {error && (
        <p className="text-xs text-red-600 mt-1">{error}</p>
      )}
      <p className="text-xs text-gray-500 mt-1">Format: dd/mm/yyyy (e.g., 21/02/2026)</p>
    </div>
  );
}
