import React, { useState } from 'react';
import * as api from '../services/api';
import { useAuth } from '../hooks/useAuth';

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const response = await api.login({ username, password });
      login(response.access_token);
      // CORREÇÃO: Usa um redirecionamento completo do navegador para forçar a
      // reinicialização da aplicação e a atualização de todos os componentes,
      // incluindo a Sidebar, que agora lerá o novo estado de autenticação.
      globalThis.location.href = '/history';
    } catch (err: any) {
      setError(err.response?.data?.error || 'Falha no login. Verifique suas credenciais.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>Acesso Administrativo</h2>
      <p>Faça o login para gerenciar os relatórios.</p>
      
      {error && <div className="error-message mb-4">{error}</div>}

      <form onSubmit={handleSubmit} className="login-form">
        <div className="form-group">
          <label htmlFor="username">Usuário</label>
          <input type="text" id="username" value={username} onChange={(e) => setUsername(e.target.value)} required />
        </div>
        <div className="form-group">
          <label htmlFor="password">Senha</label>
          <input type="password" id="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
    </div>
  );
};

export default LoginPage;
