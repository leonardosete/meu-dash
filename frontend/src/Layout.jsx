/* eslint-disable react/prop-types */
import { NavLink } from 'react-router-dom';

function Layout({ children }) {
  return (
    <div className="main-layout">
      <header className="main-header">
        <nav>
          <ul>
            <li><NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>Dashboard</NavLink></li>
            <li><NavLink to="/history" className={({ isActive }) => isActive ? 'active' : ''}>Histórico</NavLink></li>
            {/* Adicionar link de Login/Logout aqui futuramente */}
          </ul>
        </nav>
      </header>
      <main>
        {children}
      </main>
    </div>
  );
}

export default Layout;