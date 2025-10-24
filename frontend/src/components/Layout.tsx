import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';

const Layout: React.FC = () => {
  const location = useLocation();

  return (
    <div className="layout-wrapper">
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