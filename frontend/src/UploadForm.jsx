/* eslint-disable react/prop-types */
import { useState } from 'react';
import { uploadFile } from '../services/api';
import Spinner from './Spinner';

function UploadForm({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle'); // 'idle', 'uploading', 'success', 'error'
  const [message, setMessage] = useState('');

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
    setStatus('idle');
    setMessage('');
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file) {
      setMessage('Por favor, selecione um arquivo.');
      setStatus('error');
      return;
    }

    setStatus('uploading');
    setMessage('Enviando arquivo...');

    try {
      const result = await uploadFile(file);
      setStatus('success');
      setMessage(`Upload bem-sucedido! Relatório disponível em:`);
      // Chama a função do pai para recarregar os dados do dashboard
      if (onUploadSuccess) {
        onUploadSuccess(result);
      }
    } catch (error) {
      setStatus('error');
      setMessage(error.message || 'Falha no upload.');
    }
  };

  return (
    <section className="upload-section">
      <h2>Novo Upload de Análise</h2>
      <form onSubmit={handleSubmit}>
        <input type="file" onChange={handleFileChange} accept=".csv" />
        <button type="submit" disabled={status === 'uploading'}>
          {status === 'uploading' ? 'Enviando...' : 'Enviar Arquivo'}
        </button>
      </form>
      {status === 'uploading' && <Spinner />}
      {message && (
        <div
          className={`upload-status ${status === 'error' ? 'error' : ''}`}
          role={status === 'error' ? 'alert' : 'status'}
        >
          <p>{message}</p>
        </div>
      )}
    </section>
  );
}

export default UploadForm;