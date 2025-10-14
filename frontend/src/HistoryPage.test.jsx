import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import HistoryPage from './HistoryPage';
import * as api from '../services/api';

vi.mock('../services/api');

const mockReports = {
  reports: [
    { id: 1, created_at: '2025-10-26T10:00:00Z', report_url: '/reports/1.html' },
    { id: 2, created_at: '2025-10-25T11:00:00Z', report_url: '/reports/2.html' },
  ],
};

describe('HistoryPage', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    // Mock da função window.confirm para sempre retornar true nos testes
    window.confirm = vi.fn(() => true);
  });

  it('exibe a lista de relatórios após o carregamento', async () => {
    api.fetchAllReports.mockResolvedValue(mockReports);
    render(<HistoryPage />);

    expect(await screen.findByText('Histórico de Relatórios')).toBeInTheDocument();
    expect(screen.getByText('ID')).toBeInTheDocument();
    
    // Verifica se os dois relatórios estão na tabela
    const reportLinks = await screen.findAllByText('Ver Relatório');
    expect(reportLinks).toHaveLength(2);
  });

  it('chama a função de deletar e remove o item da lista ao clicar no botão', async () => {
    const user = userEvent.setup();
    api.fetchAllReports.mockResolvedValue(mockReports);
    api.deleteReport.mockResolvedValue({ message: 'Relatório deletado com sucesso.' });

    render(<HistoryPage />);

    // Espera a tabela carregar
    const deleteButtons = await screen.findAllByRole('button', { name: /deletar/i });
    expect(deleteButtons).toHaveLength(2);

    // Clica no botão de deletar do primeiro relatório (ID 1)
    await user.click(deleteButtons[0]);

    // Verifica se a confirmação foi chamada
    expect(window.confirm).toHaveBeenCalledWith('Tem certeza que deseja deletar o relatório ID 1?');

    // Verifica se a API de delete foi chamada com os parâmetros corretos
    expect(api.deleteReport).toHaveBeenCalledWith(1, expect.any(String));

    // Espera a UI ser atualizada
    await waitFor(() => {
      // Apenas um botão de deletar deve permanecer
      expect(screen.getAllByRole('button', { name: /deletar/i })).toHaveLength(1);
      // O relatório com ID 1 não deve mais estar na tela
      expect(screen.queryByText('26/10/2025, 07:00:00')).toBeNull();
    });
  });
});