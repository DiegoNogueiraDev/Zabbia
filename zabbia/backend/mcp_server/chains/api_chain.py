import os
import json
import aiohttp
from typing import Dict, Any
import re

class APIGenerationChain:
    def __init__(self):
        self.openrouter_endpoint = "https://openrouter.ai/api/v1/chat/completions"
        self.default_model = "openai/gpt-4o-mini"
        
        # Carregar sistema de prompts
        self.system_prompt = """Você é um especialista em API JSON-RPC do Zabbix.
Sua tarefa é converter instruções em linguagem natural para chamadas válidas para a API do Zabbix.

Siga estas diretrizes:
1. Gere apenas objetos JSON válidos para a API JSON-RPC do Zabbix 6.0
2. Inclua todos os campos obrigatórios: jsonrpc, method, params e id
3. Use o valor "2.0" para jsonrpc e um número inteiro para id
4. Estruture o objeto "params" conforme a documentação da API Zabbix
5. Para filtros, use objetos aninhados com chaves e valores apropriados
6. Inclua apenas os parâmetros necessários para a operação solicitada

Métodos comuns da API Zabbix:
- host.get - Obtém informações sobre hosts
- item.get - Obtém informações sobre itens
- history.get - Obtém valores históricos de itens
- trigger.get - Obtém informações sobre triggers
- event.get - Obtém informações sobre eventos
- problem.get - Obtém informações sobre problemas ativos
- user.get - Obtém informações sobre usuários
- graph.get - Obtém informações sobre gráficos

Exemplos de filtros:
- filter: { "host": ["web01", "web02"] } - filtra por nomes de hosts
- search: { "name": "CPU usage" } - busca pelo nome do item
- searchWildcardsEnabled: true - permite o uso de wildcards em search

Em sua resposta, forneça APENAS o objeto JSON formado sem nenhuma explicação.
"""
    
    async def run(self, action: str, api_key: str) -> Dict[str, Any]:
        """
        Executa a chain de geração de chamada de API com o OpenRouter.
        """
        # Preparar mensagens para o modelo
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": action}
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
                "temperature": 0.1,
                "max_tokens": 1000
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
                api_response = response_data["choices"][0]["message"]["content"]
                
                # Extrair JSON se estiver em um bloco de código
                json_match = re.search(r"```json\n(.*?)```", api_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1).strip()
                else:
                    # Se não estiver em um bloco de código, usar a resposta completa
                    json_str = api_response.strip()
                
                try:
                    api_call = json.loads(json_str)
                    return api_call
                except json.JSONDecodeError as e:
                    raise ValueError(f"Erro ao decodificar JSON: {str(e)}") 