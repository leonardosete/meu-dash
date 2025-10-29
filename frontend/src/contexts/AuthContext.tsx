import { createContext } from "react";

interface AuthContextType {
  token: string | null;
  isAuthenticated: boolean;
  isInitializing: boolean;
  login: (newToken: string) => void;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType>({
  token: null,
  isAuthenticated: false,
  isInitializing: true,
  login: () => {},
  logout: () => {},
});