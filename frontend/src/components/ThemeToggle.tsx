import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      className="theme-toggle-button"
      onClick={toggleTheme}
    >
      {theme === 'light' ? <Moon /> : <Sun />}
    </button>
  );
};

export default ThemeToggle;