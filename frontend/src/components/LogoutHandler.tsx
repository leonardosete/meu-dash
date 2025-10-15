import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const LogoutHandler: React.FC = () => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    logout();
    navigate('/'); // Redireciona para a página inicial após o logout
  }, [logout, navigate]);

  return null; // Este componente não renderiza nada
};

export default LogoutHandler;