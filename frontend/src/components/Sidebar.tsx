import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, PieChart, Code, History, LayoutDashboard, LogOut } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { API_BASE_URL } from '../services/api';

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
    // Constrói a URL completa para o backend e navega na mesma aba
    return <a href={`${API_BASE_URL}${to}`} className="card side-card">{content}</a>;
  }

  return <Link to={to} className="card side-card">{content}</Link>;
};

const Sidebar = () => {
  const { isAuthenticated, logout } = useAuth();

  return (
    <aside className="sidebar-column">
      <SideCard 
        to="/" 
        icon={<LayoutDashboard />} 
        title="Dashboard Principal" 
        description="Voltar para a tela inicial." 
        color="var(--accent-color)" 
      />

      {isAuthenticated ? (
        <SideCard to="/admin/logout" icon={<LogOut />} title="Modo Admin Ativo" description="Clique para sair" color="var(--danger-color)" />
      ) : (
        <SideCard to="/admin/login" icon={<Shield />} title="Acesso Administrativo" description="Login para gerenciar relatórios" color="var(--warning-color)" />
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
    </aside>
  );
};

export default Sidebar;