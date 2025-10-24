import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shield, PieChart, Code, History, LayoutDashboard, LogOut } from 'lucide-react';
import { API_BASE_URL } from '../services/api'; // Importa a URL base da API
import { useAuth } from '../hooks/useAuth';

interface SideCardProps {
  to: string;
  icon: React.ReactElement;
  title: string;
  description: string;
  color: string;
  isExternal?: boolean;
}

const SideCard: React.FC<SideCardProps> = ({ to, icon, title, description, color, isExternal = false }) => {
  const content = (
    <>
      {React.cloneElement(icon, { color })}
      <div className="side-card-text">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </>
  );

  if (isExternal) {
    // CORREÇÃO: Se a API_BASE_URL for uma string vazia (como em produção),
    // usamos o caminho 'to' diretamente. Caso contrário, construímos a URL completa.
    const externalUrl = API_BASE_URL ? new URL(to, API_BASE_URL).href : to;
    
    // Adiciona target="_blank" para abrir em uma nova aba
    // rel="noopener noreferrer" é uma boa prática de segurança para links externos
    return (
      <a href={externalUrl} className="card side-card" target="_blank" rel="noopener noreferrer">
        {content}
      </a>
    );
  }

  return <Link to={to} className="card side-card">{content}</Link>;
};

const Sidebar = () => {
  const location = useLocation();

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
      <SideCard 
        to="/docs/doc_gerencial.html" 
        isExternal={true}
        icon={<PieChart />} 
        title="Documentação Gerencial" 
        description="Visão de negócio e conceitos." 
        color="var(--accent-color)" 
      />
      <SideCard 
        // O link aponta para a rota raiz do Flasgger no backend.
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

      {/* MELHORIA DE UX: O card de login/logout é movido para o final e separado visualmente */}
      <div className="sidebar-footer">
        {/* Adiciona o número da versão no rodapé da sidebar */}
        <div className="sidebar-version">
          v{import.meta.env.VITE_APP_VERSION}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;