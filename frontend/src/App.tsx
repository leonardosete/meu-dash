import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import HistoryPage from './components/HistoryPage';
import LoginPage from './components/LoginPage';
import Layout from './components/Layout'; // Importa o novo layout
import LogoutHandler from './components/LogoutHandler';

function App() {
  return (
    <Router>
      <div className="bg-gray-900 text-gray-100 min-h-screen">
        <Routes>
          {/* Rotas que usam o layout principal com a barra lateral */}
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="history" element={<HistoryPage />} />
          </Route>
          {/* Rotas de autenticação que são páginas independentes */}
          <Route path="admin/login" element={<LoginPage />} />
          <Route path="admin/logout" element={<LogoutHandler />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;