import React, {
  createContext,
  useState,
  useCallback,
  ReactNode,
  useEffect,
} from "react";

const TOKEN_KEY = "meu_dash_auth_token";

interface AuthContextType {
  token: string | null;
  isAuthenticated: boolean;
  isInitializing: boolean;
  login: (newToken: string) => void;
  logout: () => void;
}

// Exporta o Context para que o hook possa usá-lo
export const AuthContext = createContext<AuthContextType>({
  token: null,
  isAuthenticated: false,
  isInitializing: true,
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
    try {
      const storedToken = localStorage.getItem(TOKEN_KEY);
      setToken(storedToken);
    } catch (error) {
      console.error("Falha ao acessar o localStorage:", error);
      setToken(null);
    } finally {
      setIsInitializing(false);
    }

    const handleAuthError = () => {
      logout();
    };
    window.addEventListener("auth-error", handleAuthError);

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