import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  PieChart,
  Code,
  History,
  LayoutDashboard,
  LogOut,
  FilePlus2,
} from "lucide-react";
import { API_BASE_URL } from "../services/api";
import { useAuth } from "../contexts/AuthContext";
import { useDashboard } from "../contexts/DashboardContext";
import ThemeToggle from "./ThemeToggle";

interface SideCardProps {
  to?: string;
  onClick?: () => void;
  icon: React.ReactElement;
  title: string;
  description: string;
  color: string;
  isExternal?: boolean;
}

const SideCard: React.FC<SideCardProps> = ({
  to,
  onClick,
  icon,
  title,
  description,
  color,
  isExternal = false,
}) => {
  const content = (
    <>
      {React.cloneElement(icon, { color })}
      <div className="side-card-tooltip">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </>
  );

  const commonProps = {
    className: "card side-card",
    title: "", // Adicionado para sobrescrever o tooltip nativo
  };

  if (onClick) {
    return (
      <button onClick={onClick} {...commonProps}>
        {content}
      </button>
    );
  }

  if (isExternal) {
    const externalUrl = to
      ? API_BASE_URL
        ? new URL(to, API_BASE_URL).href
        : to
      : "#";
    return (
      <a
        href={externalUrl}
        target="_blank"
        rel="noopener noreferrer"
        {...commonProps}
      >
        {content}
      </a>
    );
  }

  return (
    <Link to={to || "#"} {...commonProps}>
      {content}
    </Link>
  );
};

const Sidebar: React.FC = () => {
  const location = useLocation();
  const { isAuthenticated, logout } = useAuth();
  const { reportUrls, setReportUrls } = useDashboard();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <aside className="sidebar-column">
      <div className="sidebar-header">
        <h2 className="sidebar-title">Menu</h2>
      </div>

      <div className="sidebar-cards-container">
        {location.pathname !== "/" && (
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
          to="/history"
          icon={<History />}
          title="Histórico de Análises"
          description="Visualize e gerencie todos os relatórios."
          color="var(--text-color)"
        />
        <SideCard
          to="/docs/doc_gerencial.html"
          isExternal={true}
          icon={<PieChart />}
          title="Documentação Gerencial"
          description="Conhecendo a ferrementa."
          color="var(--accent-color)"
        />
        <SideCard
          to="/apidocs/"
          isExternal={true}
          icon={<Code />}
          title="Documentação da API"
          description="Navegue e teste os endpoints (Swagger)."
          color="#38bdf8"
        />
      </div>

      <div className="sidebar-footer">
        {isAuthenticated && (
          <SideCard
            onClick={handleLogout}
            icon={<LogOut />}
            title="Sair do Modo Admin"
            description="Desconectar da sessão administrativa."
            color="var(--danger-color)"
          />
        )}
        <ThemeToggle />
        <div className="sidebar-version">
          v{import.meta.env.VITE_APP_VERSION}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;