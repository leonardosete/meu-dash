import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import * as api from '../services/api';
import { Loader2 } from 'lucide-react';

const InlineLoginForm: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.login({ username, password });
      login(response.access_token);
      // O componente pai (UploadForms) se tornará visível reativamente
    } catch (err: any) {
      setError(err.response?.data?.error || 'Falha na autenticação.');
      setIsLoading(false);
    }
  };

  return (
    <div className="inline-login-form-container">
      <h3>Acesso Administrativo</h3>
      {error && <div className="error-message small">{error}</div>}
      <form onSubmit={handleSubmit} className="inline-login-form">
        <div className="input-group">
          <label htmlFor="inline-username">Usuário</label>
          <input
            id="inline-username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoFocus
          />
        </div>
        <div className="input-group">
          <label htmlFor="inline-password">Senha</label>
          <input
            id="inline-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit" disabled={isLoading}>
          {isLoading ? <Loader2 className="animate-spin" /> : 'Entrar'}
        </button>
      </form>
    </div>
  );
};

export default InlineLoginForm;