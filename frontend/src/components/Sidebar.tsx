import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shield, PieChart, Code, History, LayoutDashboard, LogOut, FilePlus2 } from 'lucide-react';
import { API_BASE_URL } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { useDashboard } from '../contexts/DashboardContext';

interface SideCardProps {
  to?: string;
  onClick?: () => void;
  icon: React.ReactElement;
  title: string;
  description: string;
  color: string;
  isExternal?: boolean;
}

const SideCard: React.FC<SideCardProps> = ({ to, onClick, icon, title, description, color, isExternal = false }) => {
  const content = (
    <>
      {React.cloneElement(icon, { color })}
      <div className="side-card-text">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </>
  );

  if (onClick) {
    return (
      <button onClick={onClick} className="card side-card">
        {content}
      </button>
    );
  }

  if (isExternal) {
    const externalUrl = to ? (API_BASE_URL ? new URL(to, API_BASE_URL).href : to) : '#';
    return (
      <a href={externalUrl} className="card side-card" target="_blank" rel="noopener noreferrer">
        {content}
      </a>
    );
  }

  return <Link to={to || '#'} className="card side-card">{content}</Link>;
};

const Sidebar = () => {
  const location = useLocation();
  const { isAuthenticated } = useAuth();
  const { reportUrls, setReportUrls } = useDashboard();

  return (
    <aside className="sidebar-column">
      {location.pathname !== '/' && (
        <SideCard 
          to="/" 
          icon={<LayoutDashboard />} 
          title="Dashboard Principal" 
          description="Visão geral dos KPIs e uploads." 
          color="var(--success-color)" 
        />
      )}
      
      {reportUrls && (
        <SideCard
          onClick={() => setReportUrls(null)}
          icon={<FilePlus2 />}
          title="Nova Análise"
          description="Voltar para a tela de upload."
          color="var(--success-color)"
        />
      )}

      <SideCard 
        to="/docs/doc_gerencial.html" 
        isExternal={true}
        icon={<PieChart />} 
        title="Documentação Gerencial" 
        description="Visão de negócio e conceitos." 
        color="var(--accent-color)" 
      />
      <SideCard 
        to="/apidocs" 
        isExternal={true}
        icon={<Code />} 
        title="Documentação da API" 
        description="Navegue e teste os endpoints (Swagger)." 
        color="#38bdf8"
      />
      <SideCard 
        to="/history" 
        icon={<History />} 
        title="Histórico de Análises Padrão" 
        description="Visualize e gerencie todos os relatórios." 
        color="var(--text-color)"
      />

      <div className="sidebar-footer">
        {isAuthenticated && (
          <SideCard
            to="/admin/logout"
            icon={<LogOut />}
            title="Sair do Modo Admin"
            description="Desconectar da sessão administrativa."
            color="var(--danger-color)"
          />
        )}
        <div className="sidebar-version">
          v{import.meta.env.VITE_APP_VERSION}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;