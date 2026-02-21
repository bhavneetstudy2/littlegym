'use client';

interface StatCardProps {
  icon: React.ReactNode;
  iconBg: string;
  label: string;
  value: string | number;
  loading?: boolean;
}

export default function StatCard({ icon, iconBg, label, value, loading }: StatCardProps) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${iconBg}`}>{icon}</div>
      <div>
        <p className="stat-label">{label}</p>
        {loading ? (
          <div className="skeleton h-7 w-16 mt-1" />
        ) : (
          <p className="stat-value">{value}</p>
        )}
      </div>
    </div>
  );
}
