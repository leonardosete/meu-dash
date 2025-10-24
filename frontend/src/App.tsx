import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import HistoryPage from './components/HistoryPage';
import Layout from './components/Layout';
import { AuthProvider } from './contexts/AuthContext';
import { useAuth } from './hooks/useAuth';
import { Loader2 } from 'lucide-react';
import { DashboardProvider } from './contexts/DashboardContext';
import { SidebarProvider } from './contexts/SidebarContext';

// Componente intermediário que aguarda a inicialização do estado de autenticação
const AppRoutes: React.FC = () => {
  const { isInitializing } = useAuth();

  // Se o estado de autenticação ainda não foi verificado, exibe um loader.
  // Isso impede que a UI seja renderizada em um estado incorreto.
  if (isInitializing) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Loader2 className="animate-spin" size={48} />
      </div>
    );
  }

  // Após a inicialização, renderiza as rotas normalmente.
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="history" element={<HistoryPage />} />
      </Route>
    </Routes>
  );
};

function App() {
  return (
    <Router>
      <AuthProvider>
        <DashboardProvider>
          <SidebarProvider>
            <div className="app-container">
              <AppRoutes />
            </div>
          </SidebarProvider>
        </DashboardProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;