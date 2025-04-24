// API base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Função auxiliar para chamadas de API
async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  try {
    // Adicionar licença nos cabeçalhos, se disponível
    const licenseKey = typeof window !== 'undefined' ? localStorage.getItem("zabbia_license") : null;
    const headers = {
      "Content-Type": "application/json",
      ...(licenseKey ? { "X-License-Key": licenseKey } : {}),
      ...(options?.headers || {})
    };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers
    });

    // Verificar se a resposta foi bem-sucedida
    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: `Erro HTTP ${response.status}` }));
      throw new Error(error.detail || error.message || `Erro HTTP ${response.status}`);
    }

    // Analisar resposta JSON
    const data = await response.json();
    return data as T;
  } catch (error) {
    console.error(`Erro na API: ${endpoint}`, error);
    throw error;
  }
}

// Endpoints de métricas
export async function fetchMetricsOverview() {
  return fetchAPI("/api/metrics/overview");
}

export async function fetchHostMetrics(host: string, fromDate?: Date, toDate?: Date) {
  let url = `/api/metrics/${host}`;
  const params = new URLSearchParams();
  
  if (fromDate) {
    params.append("from", fromDate.toISOString());
  }
  
  if (toDate) {
    params.append("to", toDate.toISOString());
  }
  
  const paramsString = params.toString();
  if (paramsString) {
    url += `?${paramsString}`;
  }
  
  return fetchAPI(url);
}

export async function fetchHighCpuHosts(threshold = 80, periodMinutes = 30) {
  return fetchAPI(`/api/metrics/high-cpu?threshold=${threshold}&period_minutes=${periodMinutes}`);
}

// Endpoints de chat
export async function sendChatMessage(messages: any[]) {
  return fetchAPI("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      messages,
      user_id: "default_user" // Em produção, usar ID do usuário autenticado
    })
  });
}

export async function fetchChatHistory(userId = "default_user", limit = 10) {
  return fetchAPI(`/api/chat/history/${userId}?limit=${limit}`);
}

// Endpoints de configurações
export async function saveZabbixSettings(settings: {
  url: string;
  username: string;
  password: string;
  api_token?: string;
}) {
  return fetchAPI("/api/settings/zabbix", {
    method: "POST",
    body: JSON.stringify(settings)
  });
}

export async function getZabbixSettings() {
  return fetchAPI("/api/settings/zabbix");
}

export async function saveOpenRouterKey(settings: { api_key: string }) {
  return fetchAPI("/api/settings/openrouter", {
    method: "POST",
    body: JSON.stringify(settings)
  });
}

export async function checkOpenRouterSettings() {
  return fetchAPI("/api/settings/openrouter");
}

// Endpoints de licença
export async function validateLicense(licenseKey: string) {
  return fetchAPI("/api/license/validate", {
    method: "POST",
    body: JSON.stringify({ license_key: licenseKey })
  });
}

export async function saveLicense(licenseKey: string) {
  return fetchAPI("/api/license/save", {
    method: "POST",
    body: JSON.stringify({ license_key: licenseKey })
  });
} 