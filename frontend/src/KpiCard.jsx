/* eslint-disable react/prop-types */
function KpiCard({ title, value }) {
    return (
      <div className="kpi-card">
        <h3>{title}</h3>
        <p className="value">{value}</p>
      </div>
    );
  }
  
  export default KpiCard;