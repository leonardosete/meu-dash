import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useSidebar } from '../contexts/SidebarContext';

const Layout: React.FC = () => {
  const location = useLocation();
  const { isCollapsed } = useSidebar();

  return (
    <div className={`layout-wrapper ${isCollapsed ? 'sidebar-collapsed' : ''}`}>
      <Sidebar />
      <div className="content-wrapper">
        <main className="main-content page-fade-in" key={location.pathname}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;