import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Shield, LogOut } from 'lucide-react';

const Header: React.FC = () => {
  const { isAuthenticated, logout } = useAuth();

  const handleLogout = () => {
    logout();
    globalThis.location.href = '/';
  };

  return (
    <header className="main-header">
      <div className="header-content">
        {/* Espaço reservado para futuro título ou breadcrumbs */}
        <div />
        {isAuthenticated ? (
          <button type="button" className="admin-button has-tooltip" data-tooltip="Sair do Modo Admin" onClick={handleLogout}>
            <LogOut size={20} color="var(--danger-color)" />
            <span>Sair</span>
          </button>
        ) : (
          <Link to="/admin/login" className="admin-button has-tooltip" data-tooltip="Acesso Administrativo">
            <Shield size={20} color="var(--warning-color)" />
          </Link>
        )}
      </div>
    </header>
  );
};

export default Header;