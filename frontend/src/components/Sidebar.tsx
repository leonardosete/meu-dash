import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  PieChart,
  Code,
  History,
  LayoutDashboard,
  LogOut,
  FilePlus2,
  MessageSquare,
} from "lucide-react";
import { resolveApiUrl } from "../services/api";
import { useAuth } from "../hooks/useAuth";
import { useDashboard } from "../hooks/useDashboard";
import ThemeToggle from "./ThemeToggle";
import FeedbackModal from "./FeedbackModal";

interface SideCardProps {
  to?: string;
  onClick?: () => void;
  icon: React.ReactElement;
  title: string;
  description: string;
  color: string;
  isExternal?: boolean;
  disabled?: boolean;
}

const SideCard: React.FC<SideCardProps> = ({
  to,
  onClick,
  icon,
  title,
  description,
  color,
  isExternal = false,
  disabled = false,
}) => {
  // AJUSTE 2 & 3: Se desabilitado, o ícone fica cinza e o card recebe estilos de desativado
  const iconColor = disabled ? "var(--text-secondary-color)" : color;

  const content = (
    <>
      {React.cloneElement(icon, { color: iconColor })}
      <div className="side-card-tooltip">
        <h3>{title} {disabled && "(Em Breve)"}</h3>
        <p>{description}</p>
      </div>
    </>
  );

  const commonProps = {
    className: `card side-card ${disabled ? "disabled" : ""}`,
    title: "",
    // AJUSTE 2 & 3: Estilos inline para "escurecer" e desabilitar o clique no card
    style: disabled
      ? { 
          cursor: "not-allowed", 
          opacity: 0.5, // Mais escurecido
          filter: "grayscale(0.8)", // Remove um pouco da cor
          pointerEvents: "none" as const // Impede cliques no card
        }
      : {},
    "aria-disabled": disabled,
  };

  // AJUSTE 1: Se desabilitado, renderiza uma div para manter o layout e o ícone visíveis
  if (disabled) {
    return (
      <div {...commonProps} style={{ ...commonProps.style, pointerEvents: "auto" }}>
        {/* pointerEvents: auto aqui permite que o tooltip (filho) ainda apareça no hover,
            mesmo com o card desabilitado */}
        {content}
      </div>
    );
  }

  if (onClick) {
    return (
      <button onClick={onClick} {...commonProps}>
        {content}
      </button>
    );
  }

  if (isExternal) {
    const externalUrl = to ? resolveApiUrl(to) : "#";
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
  const [isFeedbackModalOpen, setIsFeedbackModalOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <>
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

          {/* AJUSTE 4: Trocado de lugar com a Doc Gerencial */}
          <SideCard
            to="/apidocs/"
            isExternal={true}
            icon={<Code />}
            title="Documentação da API"
            description="Navegue e teste os endpoints (Swagger)."
            color="#38bdf8"
          />

          {/* AJUSTE 4: Agora este botão vem POR ÚLTIMO */}
          <SideCard
            to="/docs/doc_gerencial.html"
            isExternal={true}
            icon={<PieChart />}
            title="Documentação Gerencial"
            description="Documentação em desenvolvimento."
            color="var(--accent-color)"
            disabled={true} // AJUSTE 2 & 3: Botão desativado
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
          <button
            className="feedback-button"
            onClick={() => setIsFeedbackModalOpen(true)}
            title=""
            type="button"
          >
            <MessageSquare />
            <span>Feedback</span>
            <div className="side-card-tooltip">
              <h3>Enviar Feedback</h3>
              <p>Compartilhe sugestões, reporte bugs ou peça melhorias.</p>
            </div>
          </button>
          <ThemeToggle />
        </div>
      </aside>
      <FeedbackModal
        isOpen={isFeedbackModalOpen}
        onClose={() => setIsFeedbackModalOpen(false)}
      />
    </>
  );
};

export default Sidebar;