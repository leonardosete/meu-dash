import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Dashboard from './Dashboard';
import * as api from '../services/api';

// Mock do módulo da API
vi.mock('../services/api');

const mockData = {
  kpi_summary: {
    total_casos: 150,
    casos_atuacao: 25,
    casos_instabilidade: 10,
    taxa_sucesso_automacao: '83.33%',
  },
  trend_history: [],
  last_action_plan: null,
};

describe('Dashboard', () => {
  beforeEach(() => {
    // Limpa os mocks antes de cada teste
    vi.resetAllMocks();
  });

  it('exibe o spinner de carregamento inicialmente', () => {
    api.fetchDashboardSummary.mockReturnValue(new Promise(() => {})); // Promessa que nunca resolve
    render(<Dashboard />);
    expect(screen.getByRole('status', { name: /carregando/i })).toBeInTheDocument();
  });

  it('exibe os dados dos KPIs após o carregamento bem-sucedido', async () => {
    api.fetchDashboardSummary.mockResolvedValue(mockData);
    render(<Dashboard />);

    // Espera que os dados sejam carregados e renderizados
    await waitFor(() => {
      expect(screen.getByText('Total de Casos Analisados')).toBeInTheDocument();
    });

    expect(screen.getByText('150')).toBeInTheDocument();
    expect(screen.getByText('25')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByText('83.33%')).toBeInTheDocument();
  });

  it('exibe uma mensagem de erro em caso de falha na API', async () => {
    const errorMessage = 'Falha na rede';
    api.fetchDashboardSummary.mockRejectedValue(new Error(errorMessage));
    render(<Dashboard />);

    // Espera que a mensagem de erro seja exibida
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    expect(screen.getByText(`Erro ao buscar dados: ${errorMessage}`)).toBeInTheDocument();
  });
});