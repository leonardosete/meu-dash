const API_BASE_URL = '/api/v1';

export async function fetchDashboardSummary() {
  const response = await fetch(`${API_BASE_URL}/dashboard-summary`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ message: 'Erro desconhecido na API' }));
    throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
    // Não defina o 'Content-Type' header, o navegador o fará
    // automaticamente com o boundary correto para multipart/form-data.
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ message: 'Erro ao processar o upload.' }));
    throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export async function fetchAllReports() {
  const response = await fetch(`${API_BASE_URL}/reports`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ message: 'Erro ao buscar relatórios.' }));
    throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export async function deleteReport(reportId, adminToken) {
  const response = await fetch(`${API_BASE_URL}/reports/${reportId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${adminToken}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ message: 'Erro ao deletar relatório.' }));
    throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export async function loginUser(credentials) {
  const response = await fetch(`/admin/login`, { // Assuming this is the backend login route
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ message: 'Credenciais inválidas.' }));
    throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}