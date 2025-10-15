import React from 'react';

interface KpiCardProps {
  title: string;
  value: string | number;
  subValue?: string | number;
  subLabel?: string;
  colorClass: string;
  borderClass: string;
}

const KpiCard: React.FC<KpiCardProps> = ({ title, value, subValue, subLabel, colorClass, borderClass, url }) => {
  const content = (
    <div className={`card kpi-card ${borderClass}`}>
      <h3 className="kpi-title">{title}</h3>
      <p className={`kpi-value ${colorClass}`}>{value}</p>
      {subValue && (
        <p className="kpi-sub-value">
          {subValue} <span className="kpi-sub-label">{subLabel}</span>
        </p>
      )}
    </div>
  );

  return content;
};

export default KpiCard;