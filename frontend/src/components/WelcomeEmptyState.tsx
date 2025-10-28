import React from 'react';
import { Rocket } from 'lucide-react';

const WelcomeEmptyState: React.FC = () => {
  return (
    <div className="welcome-empty-state">
      <Rocket size={48} className="text-accent" />
      <h2>Bem-vindo ao SmartRemedy!</h2>
      <p>Sua central de análise está pronta para começar.</p>
      <p>Para visualizar seus KPIs, faça o upload do seu primeiro arquivo de dados no formulário de <strong>Análise Padrão</strong> abaixo.</p>
    </div>
  );
};

export default WelcomeEmptyState;