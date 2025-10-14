import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('App', () => {
  it('renders the main heading', () => {
    // Renderiza o componente
    render(<App />);

    // Procura por um elemento que tenha o texto "Vite + React"
    // A opção 'name' procura por elementos com um "accessible name", que para headings é o seu conteúdo.
    expect(screen.getByRole('heading', { name: /vite \+ react/i })).toBeInTheDocument();
  });
});