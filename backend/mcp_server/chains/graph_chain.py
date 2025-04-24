import os
import json
import aiohttp
from typing import Dict, Any, List
import re

class GraphGenerationChain:
    def __init__(self):
        self.openrouter_endpoint = "https://openrouter.ai/api/v1/chat/completions"
        self.default_model = "openai/gpt-4o-mini"
        
        # Carregar sistema de prompts
        self.system_prompt = """Você é um especialista em visualização de dados do Zabbix.
Sua tarefa é gerar um objeto JSON que represente dados para um gráfico Recharts baseado na pergunta do usuário.

Siga estas diretrizes:
1. Gere apenas objetos JSON válidos que possam ser usados diretamente pelo Recharts
2. Use o formato {"chartType": "<tipo>", "labels": [<eixoX>], "datasets": [<dados>]}
3. Suporte estes tipos de gráficos: line, area, bar, pie, radar
4. Para dados de série temporal, use timestamps ISO 8601 como labels
5. Use datasets com propriedades name, data e color (em formato hex)
6. Adicione configurações específicas para cada tipo de gráfico

O usuário espera que você gere um objeto JSON que possa ser usado diretamente para renderizar
um gráfico Recharts baseado na métrica solicitada. As métricas comuns do Zabbix incluem:
- CPU usage (%)
- Memory usage (bytes ou %)
- Disk space (bytes ou %)
- Network traffic (bytes/s)
- IOPS (operations/s)
- Response time (ms)
- Uptime (%)

Configure o gráfico para mostrar dados dos últimos 7 dias, com pelo menos 20 pontos de dados.
Gere dados realistas que se assemelham ao comportamento esperado em sistemas reais.

Em sua resposta, forneça APENAS o objeto JSON sem nenhuma explicação.
"""
    
    async def run(self, query: str, api_key: str) -> Dict[str, Any]:
        """
        Executa a chain de geração de dados para gráfico com o OpenRouter.
        """
        # Preparar mensagens para o modelo
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query}
        ]
        
        # Fazer a chamada para o OpenRouter
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.default_model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            async with session.post(
                self.openrouter_endpoint,
                headers=headers,
                json=payload
            ) as response:
                response_data = await response.json()
                
                if "error" in response_data:
                    raise ValueError(f"Erro do OpenRouter: {response_data['error']}")
                
                # Extrair resposta
                graph_response = response_data["choices"][0]["message"]["content"]
                
                # Extrair JSON se estiver em um bloco de código
                json_match = re.search(r"```json\n(.*?)```", graph_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1).strip()
                else:
                    # Se não estiver em um bloco de código, usar a resposta completa
                    json_str = graph_response.strip()
                
                try:
                    chart_data = json.loads(json_str)
                    
                    # Validar formato mínimo
                    if not isinstance(chart_data, dict):
                        raise ValueError("Dados de gráfico devem ser um objeto JSON")
                    
                    if "chartType" not in chart_data:
                        chart_data["chartType"] = "line"  # Tipo padrão
                    
                    if "labels" not in chart_data or not isinstance(chart_data["labels"], list):
                        chart_data["labels"] = []
                    
                    if "datasets" not in chart_data or not isinstance(chart_data["datasets"], list):
                        chart_data["datasets"] = []
                    
                    return chart_data
                except json.JSONDecodeError as e:
                    raise ValueError(f"Erro ao decodificar JSON: {str(e)}") 