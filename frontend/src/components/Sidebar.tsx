import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, PieChart, Code, History, LayoutDashboard, LogOut } from 'lucide-react';
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
    // Constrói a URL externa dinamicamente usando a origem da janela atual.
    // Isso garante que a URL base seja sempre a correta, tanto em produção
    // (https://smart-plan.devops-master.shop) quanto em desenvolvimento (http://127.0.0.1:5174).
    // Isso elimina a dependência de uma variável de ambiente que pode estar incorreta no build.
    const externalUrl = new URL(to, window.location.origin).href;
    return (
      <a href={externalUrl} target="_blank" rel="noopener noreferrer" className="card side-card">{content}</a>
    );
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

      {isAuthenticated ? ( // Se autenticado, mostra um botão de logout
        <div className="card side-card clickable" onClick={logout}>
          <LogOut color="var(--danger-color)" />
          <div className="side-card-text">
            <h3>Modo Admin Ativo</h3>
            <p>Clique para sair</p>
          </div>
        </div>
      ) : ( // Se não, mostra o link para a página de login
        <SideCard to="/admin/login" icon={<Shield />} title="Acesso Administrativo" description="Login para gerenciar relatórios" color="var(--warning-color)" />
      )}
      
      <SideCard 
        to="/docs/doc_gerencial.html" 
        isExternal={true} // Mantém o comportamento de link externo para a documentação
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