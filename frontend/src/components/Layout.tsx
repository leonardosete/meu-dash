import React, { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";

const Layout: React.FC = () => {
  const location = useLocation();
  const [appVersion, setAppVersion] = useState<string>("");
  const [versionError, setVersionError] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const fetchVersion = async () => {
      try {
        const response = await fetch("/health", { cache: "no-store" });
        if (!response.ok) {
          throw new Error(`Erro ao buscar versão: ${response.status}`);
        }
        const payload = await response.json();
        if (isMounted) {
          setAppVersion(payload?.version ?? "indisponível");
          setVersionError(false);
        }
      } catch (error) {
        console.error(error);
        if (isMounted) {
          setAppVersion("indisponível");
          setVersionError(true);
        }
      }
    };

    fetchVersion();

    return () => {
      isMounted = false;
    };
  }, []);

  const versionLabel = appVersion || "carregando...";

  return (
    <div className="layout-wrapper sidebar-collapsed">
      <Sidebar />
      <div className="content-wrapper">
        <main className="main-content page-fade-in" key={location.pathname}>
          <Outlet />
        </main>
        <footer className="app-footer" aria-live="polite">
          <span>
            Smart Remedy • versão {versionLabel}
            {versionError ? " (verificação indisponível)" : ""}
          </span>
        </footer>
      </div>
    </div>
  );
};

export default Layout;
