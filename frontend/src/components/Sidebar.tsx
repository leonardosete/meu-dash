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
  Info,
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
  const [appVersion, setAppVersion] = useState<string | null>(null);
  const [showVersion, setShowVersion] = useState(false);

  const handleVersionClick = async () => {
    setShowVersion(false);
    try {
      const response = await fetch(resolveApiUrl("/health"), {
        cache: "no-store",
      });
      if (!response.ok) {
        return;
      }
      const payload = await response.json();
      if (payload?.version) {
        setAppVersion(String(payload.version));
      } else {
        setAppVersion("Versão não disponível");
      }
    } catch (error) {
      console.warn("Não foi possível obter a versão da API:", error);
      setAppVersion("Erro ao buscar versão");
    } finally {
      setShowVersion(true);
    }
  };

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
          <div
            style={{
              position: "relative",
              display: "flex",
              flexDirection: "column",
              gap: "0.5rem",
              marginBottom: "0.75rem",
            }}
          >
            <button
              type="button"
              onClick={handleVersionClick}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                background: "none",
                border: "1px solid var(--border-color, #d1d5db)",
                borderRadius: "0.5rem",
                padding: "0.5rem 0.75rem",
                color: "var(--text-color)",
                cursor: "pointer",
                transition: "background-color 0.2s ease",
              }}
            >
              <Info size={18} />
              <span style={{ fontSize: "0.9rem" }}>Ver versão</span>
            </button>
            {showVersion && (
              <div
                style={{
                  position: "absolute",
                  top: "100%",
                  left: 0,
                  zIndex: 10,
                  marginTop: "0.5rem",
                  padding: "0.75rem",
                  borderRadius: "0.5rem",
                  border: "1px solid var(--border-color, #d1d5db)",
                  backgroundColor: "var(--card-bg, #fff)",
                  boxShadow: "0 4px 16px rgba(15, 23, 42, 0.12)",
                  color: "var(--text-color)",
                  minWidth: "180px",
                }}
              >
                <strong style={{ display: "block", marginBottom: "0.25rem" }}>
                  Versão do app:
                </strong>
                <span>{appVersion ?? "-"}</span>
                <button
                  type="button"
                  onClick={() => setShowVersion(false)}
                  style={{
                    marginTop: "0.5rem",
                    fontSize: "0.75rem",
                    color: "var(--accent-color, #1d4ed8)",
                    textDecoration: "underline",
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                  }}
                >
                  Fechar
                </button>
              </div>
            )}
          </div>

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
            description="Conhecendo a ferramenta."
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