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
  HelpCircle,
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
  const [showVersion, setShowVersion] = useState(false);
  const [versionMessage, setVersionMessage] = useState<string | null>(null);

  const handleVersionClick = async () => {
    setVersionMessage("Carregando...");
    setShowVersion(true);
    try {
      const response = await fetch(resolveApiUrl("/health"), {
        cache: "no-store",
        credentials: "include",
      });
      if (!response.ok) {
        setVersionMessage(`Versão não disponível (status ${response.status})`);
        return;
      }
      const payload = await response.json();
      if (payload?.version) {
        setVersionMessage(`v${String(payload.version)}`);
      } else {
        setVersionMessage("Versão não disponível");
      }
    } catch (error) {
      console.warn("Não foi possível obter a versão da API:", error);
      setVersionMessage("Erro ao buscar versão");
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

        <div
          className="sidebar-cards-container"
          style={{ position: "relative", paddingTop: "0.5rem" }}
        >
          <button
            type="button"
            onClick={handleVersionClick}
            aria-label="Ver versão do app"
            style={{
              position: "absolute",
              top: "0.5rem",
              right: "0.5rem",
              width: "28px",
              height: "28px",
              borderRadius: "999px",
              border: "1px solid var(--border-color, #d1d5db)",
              background: "var(--card-bg, #fff)",
              color: "var(--text-color)",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              boxShadow: "0 2px 8px rgba(15, 23, 42, 0.12)",
            }}
          >
            <HelpCircle size={16} />
          </button>
          {showVersion && (
            <div
              style={{
                position: "absolute",
                top: "3.25rem",
                right: "0.5rem",
                zIndex: 10,
                padding: "0.75rem",
                borderRadius: "0.5rem",
                border: "1px solid var(--border-color, #d1d5db)",
                backgroundColor: "var(--card-bg, #fff)",
                boxShadow: "0 4px 16px rgba(15, 23, 42, 0.12)",
                color: "var(--text-color)",
                minWidth: "190px",
              }}
            >
              <strong style={{ display: "block", marginBottom: "0.25rem" }}>
                Versão do app
              </strong>
              <span>{versionMessage ?? "-"}</span>
              <div style={{ marginTop: "0.5rem", textAlign: "right" }}>
                <button
                  type="button"
                  onClick={() => setShowVersion(false)}
                  style={{
                    fontSize: "0.75rem",
                    color: "var(--accent-color, #1d4ed8)",
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    textDecoration: "underline",
                  }}
                >
                  Fechar
                </button>
              </div>
            </div>
          )}

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