'use client';

interface LoadingStateProps {
  message?: string;
}

export default function LoadingState({ message = 'Loading...' }: LoadingStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <div className="spinner mb-3" />
      <p className="text-sm text-gray-500">{message}</p>
    </div>
  );
}
