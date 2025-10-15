import React from 'react';

interface KpiCardProps {
  title: string;
  value: string | number;
  subValue?: string | number;
  subLabel?: string;
  colorClass: string;
  // A prop 'borderClass' foi removida, pois a borda agora é controlada pela divisória no CSS
}

const KpiCard: React.FC<KpiCardProps> = ({ title, value, subValue, subLabel, colorClass }) => {
  // A raiz do componente não tem a classe '.card', pois o contêiner pai já a fornece
  return (
    <div className="kpi-card">
      {/* Ordem dos elementos ajustada para: Valor -> Rótulo -> Sub-Valor -> Sub-Rótulo */}
      <p className={`kpi-value ${colorClass}`}>{value}</p>
      <p className="kpi-label">{title}</p>
      
      {subValue && (
        <div className="kpi-sub-group">
            {/* A classe de cor é aplicada ao sub-valor apenas se um 'subLabel' for fornecido.
              Isso corresponde ao visual da imagem, onde '22 Alertas' é colorido, 
              mas '42 de 60 Casos' não é.
            */}
            <p className={`kpi-sub-value ${subLabel ? colorClass : ''}`}>
                {subValue}
            </p>
            {/* O sub-rótulo (ex: "Alertas") só é renderizado se existir */}
            {subLabel && <p className="kpi-sub-label">{subLabel}</p>}
        </div>
      )}
    </div>
  );
};

export default KpiCard;