import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

const Layout: React.FC = () => {
  return (
    <div className="layout-wrapper">
      <Sidebar />
      <main className="main-content-column">
        <Outlet /> {/* As páginas da rota serão renderizadas aqui */}
      </main>
    </div>
  );
};

export default Layout;