import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Loader2, ShieldCheck } from 'lucide-react';

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      await login({ username, password });
      navigate('/'); // Redireciona para o dashboard após o login
    } catch (err: any) {
      setError(err.response?.data?.error || 'Falha na autenticação. Verifique suas credenciais.');
      setIsLoading(false);
    }
  };

  return (
    <div className="login-page-container">
      <div className="login-card">
        <div className="login-header">
          <ShieldCheck size={40} className="text-accent" />
          <h2>Acesso Administrativo</h2>
          <p>Faça login para gerenciar o sistema.</p>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <label htmlFor="username">Usuário</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="input-group">
            <label htmlFor="password">Senha</label>
            <input
              id="password"
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

        <div className="login-footer">
          <Link to="/">&larr; Voltar para o Dashboard</Link>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;