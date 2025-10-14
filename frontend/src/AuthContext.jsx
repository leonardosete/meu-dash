/* eslint-disable react/prop-types */
import { createContext, useContext, useState, useEffect } from 'react';
import { loginUser } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('authToken'));

  useEffect(() => {
    // Sincroniza o estado com o localStorage
    if (token) {
      localStorage.setItem('authToken', token);
    } else {
      localStorage.removeItem('authToken');
    }
  }, [token]);

  const login = async (credentials) => {
    try {
      const data = await loginUser(credentials);
      setToken(data.access_token);
    } catch (error) {
      // O erro será tratado no componente de login
      throw error;
    }
  };

  const logout = () => {
    setToken(null);
  };

  const value = {
    token,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => {
  return useContext(AuthContext);
};