import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import UploadForm from './UploadForm';
import * as api from '../services/api';

vi.mock('../services/api');

describe('UploadForm', () => {
  it('renderiza o formulário de upload corretamente', () => {
    render(<UploadForm />);
    expect(screen.getByText('Novo Upload de Análise')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /enviar arquivo/i })).toBeInTheDocument();
  });

  it('permite ao usuário selecionar um arquivo', async () => {
    const user = userEvent.setup();
    render(<UploadForm />);
    const file = new File(['hello'], 'hello.csv', { type: 'text/csv' });
    const input = screen.getByLabelText('', { selector: 'input[type="file"]' });

    await user.upload(input, file);

    expect(input.files[0]).to.equal(file);
    expect(input.files.item(0)).to.equal(file);
    expect(input.files).toHaveLength(1);
  });

  it('mostra o estado de carregamento e chama a API ao enviar', async () => {
    const user = userEvent.setup();
    const onUploadSuccess = vi.fn();
    api.uploadFile.mockResolvedValue({ report_url: '/reports/new.html' });

    render(<UploadForm onUploadSuccess={onUploadSuccess} />);

    const file = new File(['a,b,c'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByLabelText('', { selector: 'input[type="file"]' });
    await user.upload(input, file);

    const submitButton = screen.getByRole('button', { name: /enviar arquivo/i });
    await user.click(submitButton);

    expect(screen.getByText('Enviando...')).toBeInTheDocument();
    expect(api.uploadFile).toHaveBeenCalledWith(file);

    await waitFor(() => {
      expect(screen.getByText(/upload bem-sucedido/i)).toBeInTheDocument();
      expect(onUploadSuccess).toHaveBeenCalled();
    });
  });

  it('mostra uma mensagem de erro em caso de falha no upload', async () => {
    const user = userEvent.setup();
    const errorMessage = 'O arquivo está corrompido.';
    api.uploadFile.mockRejectedValue(new Error(errorMessage));

    render(<UploadForm />);
    const file = new File(['a,b,c'], 'test.csv', { type: 'text/csv' });
    await user.upload(screen.getByLabelText('', { selector: 'input[type="file"]' }), file);
    await user.click(screen.getByRole('button', { name: /enviar arquivo/i }));

    expect(await screen.findByText(errorMessage)).toBeInTheDocument();
  });
});