import React, {
  createContext,
  useState,
  useCallback,
  ReactNode,
  useEffect,
  useContext,
} from "react";

const TOKEN_KEY = "meu_dash_auth_token";

interface AuthContextType {
  token: string | null;
  isAuthenticated: boolean;
  isInitializing: boolean; // Novo estado para controlar a verificação inicial
  login: (newToken: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  token: null,
  isAuthenticated: false,
  isInitializing: true, // A aplicação sempre começa em estado de inicialização
  login: () => {},
  logout: () => {},
});

export const AuthProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [token, setToken] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
  }, []);

  useEffect(() => {
    // Na primeira montagem, verifica o localStorage para definir o estado de autenticação.
    try {
      const storedToken = localStorage.getItem(TOKEN_KEY);
      setToken(storedToken);
    } catch (error) {
      console.error("Falha ao acessar o localStorage:", error);
      setToken(null);
    } finally {
      // Marca a inicialização como concluída, liberando a renderização da UI.
      setIsInitializing(false);
    }

    // Adiciona um listener para o evento de erro de autenticação disparado pelo interceptor da API
    const handleAuthError = () => {
      logout();
    };
    window.addEventListener("auth-error", handleAuthError);

    // Limpa o listener quando o componente é desmontado
    return () => {
      window.removeEventListener("auth-error", handleAuthError);
    };
  }, [logout]);

  const login = useCallback((newToken: string) => {
    localStorage.setItem(TOKEN_KEY, newToken);
    setToken(newToken);
  }, []);

  const isAuthenticated = !!token;

  const value = { token, isAuthenticated, isInitializing, login, logout };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth deve ser usado dentro de um AuthProvider");
  }
  return context;
};