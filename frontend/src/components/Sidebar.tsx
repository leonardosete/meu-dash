import React from 'react';
import { Link } from 'react-router-dom';
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
    const externalUrl = new URL(to, API_BASE_URL).href;
    return <a href={externalUrl} className="card side-card">{content}</a>;
  }

  return <Link to={to} className="card side-card">{content}</Link>;
};

const Sidebar = () => {
  const { isAuthenticated, logout } = useAuth();
  
  const handleLogout = () => {
    logout(); // Limpa o estado de autenticação
    // CORREÇÃO: Usa um redirecionamento completo para forçar a reinicialização
    // da aplicação e garantir que a UI reflita o estado de "não autenticado".
    globalThis.location.href = '/';
  };

  return (
    <aside className="sidebar-column">
      <SideCard 
        to="/" 
        icon={<LayoutDashboard />} 
        title="Dashboard Principal" 
        description="Voltar para a tela inicial." 
        color="var(--accent-color)" 
      />

      <SideCard 
        to="/docs/doc_gerencial.html" 
        isExternal={true} // Mantém o comportamento de link externo para a documentação
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
        {isAuthenticated ? ( // Se autenticado, mostra um botão de logout
          <button type="button" className="card side-card" onClick={handleLogout}>
            <LogOut color="var(--danger-color)" />
            <div className="side-card-text">
              <h3>Modo Admin Ativo</h3>
              <p>Clique para sair</p>
            </div>
          </button>
        ) : ( // Se não, mostra o link para a página de login
          <SideCard to="/admin/login" icon={<Shield />} title="Acesso Administrativo" description="Login para gerenciar relatórios" color="var(--warning-color)" />
        )}
      </div>
    </aside>
  );
};

export default Sidebar;