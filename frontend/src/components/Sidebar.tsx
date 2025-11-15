import React, { useCallback, useEffect, useState } from "react";
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
  const [versionStatus, setVersionStatus] = useState<"idle" | "loading" | "loaded" | "error">("idle");
  const [showVersionPopover, setShowVersionPopover] = useState(false);
  let versionLabel = "Indisponível";
  if (versionStatus === "loading") {
    versionLabel = "Carregando...";
  } else if (appVersion) {
    versionLabel = `v${appVersion}`;
  }

  const fetchVersion = useCallback(async () => {
    setVersionStatus("loading");
    try {
      const response = await fetch(resolveApiUrl("/health"), {
        cache: "no-store",
      });
      if (!response.ok) {
        setVersionStatus("error");
        return;
      }
      const payload = await response.json();
      setAppVersion(payload?.version ? String(payload.version) : null);
      setVersionStatus("loaded");
    } catch (error) {
      console.warn("Falha ao buscar versão:", error);
      setVersionStatus("error");
    }
  }, []);

  useEffect(() => {
    fetchVersion();
  }, [fetchVersion]);

  const handleToggleVersion = async () => {
    if (versionStatus === "idle" || versionStatus === "error") {
      await fetchVersion();
    }
    setShowVersionPopover((prev) => !prev);
  };

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <>
      <aside className="sidebar-column">
        <div className="sidebar-header" style={{ position: "relative" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.5rem" }}>
            <h2 className="sidebar-title" style={{ margin: 0 }}>Menu</h2>
            <button
              type="button"
              onClick={handleToggleVersion}
              aria-label="Ver versão do app"
              style={{
                width: 28,
                height: 28,
                borderRadius: "999px",
                border: "1px solid var(--border-color, #d1d5db)",
                background: "var(--card-bg, #fff)",
                color: "var(--text-color)",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
              }}
            >
              <Info size={16} />
            </button>
          </div>
          {showVersionPopover && (
            <div
              style={{
                position: "absolute",
                top: "calc(100% + 0.25rem)",
                right: 0,
                zIndex: 10,
                minWidth: 160,
                padding: "0.5rem 0.75rem",
                borderRadius: 8,
                border: "1px solid var(--border-color, #d1d5db)",
                background: "var(--card-bg, #fff)",
                boxShadow: "0 4px 12px rgba(15, 23, 42, 0.15)",
                color: "var(--text-color)",
              }}
            >
              <strong style={{ display: "block", marginBottom: 4 }}>Versão atual</strong>
              <span>{versionLabel}</span>
            </div>
          )}
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