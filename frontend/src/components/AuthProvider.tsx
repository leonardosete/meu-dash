import React, {
  useState,
  useCallback,
  ReactNode,
  useEffect,
} from "react";
import { AuthContext } from "../contexts/AuthContext";

const TOKEN_KEY = "meu_dash_auth_token";

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

export default AuthProvider;