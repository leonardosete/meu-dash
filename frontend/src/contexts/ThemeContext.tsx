import React, {
  createContext,
  useState,
  useCallback,
  ReactNode,
  useEffect,
} from "react";

type Theme = "light" | "dark";

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const THEME_KEY = "meu_dash_theme";

// Exporta o Context para que o hook possa usá-lo
export const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [theme, setTheme] = useState<Theme>("dark");

  useEffect(() => {
    try {
      const storedTheme = localStorage.getItem(THEME_KEY) as Theme | null;
      if (storedTheme && ["light", "dark"].includes(storedTheme)) {
        setTheme(storedTheme);
      }
    } catch (error) {
      console.error("Falha ao acessar o localStorage para o tema:", error);
    }
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(THEME_KEY, theme);
      document.body.classList.toggle("light-mode", theme === "light");
    } catch (error) {
      console.error("Falha ao salvar o tema no localStorage:", error);
    }
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((prevTheme) => (prevTheme === "light" ? "dark" : "light"));
  }, []);

  const value = { theme, toggleTheme };

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
};